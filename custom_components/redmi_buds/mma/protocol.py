"""MMA frame encoding and stream parsing."""

from __future__ import annotations

from dataclasses import dataclass

HEADER = b"\xfe\xdc\xba"
FOOTER = 0xEF
MAX_BODY = 1024
GET_INFO = 0x02
NOTIFY_INFO = 0x0E
SET_CONFIG = 0xF2
GET_CONFIG = 0xF3
NOTIFY_CONFIG = 0xF4


class BudsError(Exception):
    """Base exception for communication and protocol errors."""


class ProtocolError(BudsError):
    """A complete response contained malformed data."""


class ConnectionError(BudsError):
    """The local RFCOMM connection failed."""


class UnsupportedTransport(BudsError):
    """This Python platform has no Bluetooth RFCOMM socket support."""


class IncompatibleDevice(BudsError):
    """The device does not have the supported VID/PID."""


class RequestTimeout(BudsError):
    """The bounded response deadline elapsed."""


class DeviceRejected(BudsError):
    """The earbuds rejected a command."""


class WriteUnconfirmed(BudsError):
    """An attempted write could not be confirmed; do not retry automatically."""


@dataclass(frozen=True)
class Frame:
    flags: int
    opcode: int
    sequence: int
    data: bytes
    status: int | None = None

    @property
    def is_request(self) -> bool:
        return bool(self.flags & 0x80)

    @property
    def needs_reply(self) -> bool:
        return self.is_request and bool(self.flags & 0x40)


def _encode(flags: int, opcode: int, body: bytes) -> bytes:
    if not 0 <= opcode <= 255 or not 1 <= len(body) <= MAX_BODY:
        raise ValueError("Invalid MMA opcode or body length")
    return (
        HEADER
        + bytes((flags, opcode))
        + len(body).to_bytes(2, "big")
        + body
        + bytes((FOOTER,))
    )


def encode_request(opcode: int, sequence: int, payload: bytes = b"") -> bytes:
    return _encode(0xC4, opcode, bytes((sequence,)) + payload)


def encode_reply(frame: Frame, status: int = 0) -> bytes:
    """Acknowledge a request with response flags 0x00."""
    if not frame.is_request:
        raise ValueError("Only requests can be acknowledged")
    return _encode(0x00, frame.opcode, bytes((status, frame.sequence)))


class StreamParser:
    """Parse frames by length while retaining partial input."""

    def __init__(self) -> None:
        self._buffer = bytearray()

    @property
    def buffered_bytes(self) -> int:
        return len(self._buffer)

    def feed(self, data: bytes) -> list[Frame]:
        result: list[Frame] = []
        # Process input in chunks to limit buffer size.
        for offset in range(0, len(data), MAX_BODY):
            self._buffer.extend(data[offset : offset + MAX_BODY])
            while True:
                start = self._buffer.find(HEADER)
                if start < 0:
                    # Preserve a possible fragmented header prefix only.
                    keep = (
                        2
                        if self._buffer.endswith(HEADER[:2])
                        else int(self._buffer.endswith(HEADER[:1]))
                    )
                    if keep:
                        del self._buffer[:-keep]
                    else:
                        self._buffer.clear()
                    break
                if start:
                    del self._buffer[:start]
                if len(self._buffer) < 7:
                    break
                flags, opcode = self._buffer[3:5]
                size = int.from_bytes(self._buffer[5:7], "big")
                minimum = 1 if flags & 0x80 else 2
                if not minimum <= size <= MAX_BODY:
                    del self._buffer[0]
                    continue
                total = 8 + size
                if len(self._buffer) < total:
                    break
                if self._buffer[total - 1] != FOOTER:
                    del self._buffer[0]
                    continue
                body = bytes(self._buffer[7 : total - 1])
                del self._buffer[:total]
                if flags & 0x80:
                    result.append(Frame(flags, opcode, body[0], body[1:]))
                else:
                    result.append(Frame(flags, opcode, body[1], body[2:], body[0]))
        return result


def decode_blocks(data: bytes, id_size: int) -> dict[int, bytes]:
    """Decode length/type/value blocks; length includes the type bytes."""
    result: dict[int, bytes] = {}
    offset = 0
    while offset < len(data):
        size = data[offset]
        end = offset + 1 + size
        if size < id_size or end > len(data):
            raise ProtocolError("Invalid MMA block length")
        key = int.from_bytes(data[offset + 1 : offset + 1 + id_size], "big")
        if key in result:
            raise ProtocolError("Duplicate MMA block")
        result[key] = data[offset + 1 + id_size : end]
        offset = end
    return result


def config_payload(config_id: int, value: bytes) -> bytes:
    if not 0 <= config_id <= 0xFFFF or not 1 <= len(value) <= 253:
        raise ValueError("Invalid configuration value")
    return bytes((len(value) + 2,)) + config_id.to_bytes(2, "big") + value
