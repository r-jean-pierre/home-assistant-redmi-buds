"""Deterministic socket simulator. All addresses and serials are synthetic."""

from mma.protocol import StreamParser, config_payload

ADDRESS = "AA:BB:CC:DD:EE:01"
INFO = bytes.fromhex(
    "12 00 52 65 64 6d 69 20 42 75 64 73 20 36 20 50 6c 61 79 "
    "05 01 20 22 20 22 02 02 0a 05 03 27 17 50 9b "
    "02 04 01 02 05 00 03 06 02 02 04 07 e4 e4 64 02 0d 01"
)
GESTURES = bytes.fromhex("04 05 09 01 02 03 02 05 04 03 00 09")
F4 = bytes.fromhex(
    "fe dc ba c7 f4 00 10 02 0e 00 02 04 05 09 01 02 03 02 05 04 03 00 09 ef"
)
INFO_FRAME = bytes.fromhex("fe dc ba 04 02 00 36 00 0b") + INFO + b"\xef"


def response(opcode, sequence, payload=b"", status=0):
    return (
        b"\xfe\xdc\xba\x04"
        + bytes((opcode,))
        + (len(payload) + 2).to_bytes(2, "big")
        + bytes((status, sequence))
        + payload
        + b"\xef"
    )


class FakeSocket:
    def __init__(self):
        self.parser = StreamParser()
        self.sent = []
        self.pending = bytearray()
        self.config = {
            0x27: b"TEST-SERIAL-000001",
            0x2F: b"\x01",
            7: b"\x05",
            2: GESTURES,
        }
        self.info = INFO
        self.closed = False
        self.connect_error = False
        self.drop_write = False
        self.reject_write = False
        self.interleave = True
        self.connect_timeout = None
        self.timeout = None

    def settimeout(self, timeout):
        self.timeout = timeout

    def connect(self, target):
        self.target = target
        self.connect_timeout = self.timeout
        if self.connect_error:
            raise OSError("simulated connection failure")

    def sendall(self, data):
        for frame in self.parser.feed(data):
            self.sent.append(frame)
            if not frame.is_request:
                continue
            if frame.opcode == 2:
                payload = self.info
            elif frame.opcode == 0xF3:
                key = int.from_bytes(frame.data, "big")
                payload = config_payload(key, self.config[key])
            elif frame.opcode == 0xF2:
                if self.drop_write:
                    return
                if self.reject_write:
                    self.pending.extend(response(0xF2, frame.sequence, status=0xFF))
                    return
                key = int.from_bytes(frame.data[1:3], "big")
                value = frame.data[3:]
                if key == 2:
                    triplets = {
                        self.config[2][i]: self.config[2][i + 1 : i + 3]
                        for i in range(0, len(self.config[2]), 3)
                    }
                    triplets[value[0]] = value[1:]
                    # Simulate Photo coupling between single and long presses.
                    if value[0] == 4 and value[2] == 9:
                        triplets[3] = bytes((triplets[3][0], 9))
                    if value[0] == 3 and value[2] == 9:
                        triplets[4] = bytes((triplets[4][0], 9))
                    self.config[2] = b"".join(
                        bytes((k,)) + v for k, v in triplets.items()
                    )
                else:
                    self.config[key] = value
                if self.interleave:
                    notify = (
                        b"\xfe\xdc\xba\xc7\xf4"
                        + (len(config_payload(2, self.config[2])) + 1).to_bytes(
                            2, "big"
                        )
                        + bytes((frame.sequence,))
                        + config_payload(2, self.config[2])
                        + b"\xef"
                    )
                    self.pending.extend(response(0xF2, (frame.sequence + 1) % 256))
                    self.pending.extend(notify)
                payload = b""
            else:
                raise AssertionError("Unexpected opcode")
            self.pending.extend(response(frame.opcode, frame.sequence, payload))

    def recv(self, size):
        # Make every response cross socket reads and header boundaries.
        chunk = bytes(self.pending[:7])
        del self.pending[:7]
        return chunk

    def shutdown(self, how):
        self.closed = True

    def close(self):
        self.closed = True
