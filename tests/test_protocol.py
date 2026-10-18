import unittest
from dataclasses import replace

from mma.model import battery, config_value, decode_gestures, decode_info
from mma.protocol import (
    ProtocolError,
    StreamParser,
    decode_blocks,
    encode_reply,
    encode_request,
)

from .support import F4, GESTURES, INFO, INFO_FRAME, response


class ProtocolTests(unittest.TestCase):
    def test_observed_firmware_mapping_never_guesses_an_unknown_signature(self):
        info = decode_info(INFO)
        self.assertEqual(info.model_id, "M2420E1")
        self.assertEqual(info.firmware_version, "2.0.2.2")
        for raw in (None, "2022", "20232023", "20222023", "ffffffff"):
            self.assertIsNone(replace(info, firmware_raw=raw).firmware_version)
        other_model = replace(info, pid=0xFFFF)
        self.assertIsNone(other_model.model_id)
        self.assertIsNone(other_model.firmware_version)

    def test_observed_requests(self):
        cases = [
            (2, 11, b"\xff" * 4, "fe dc ba c4 02 00 05 0b ff ff ff ff ef"),
            (0xF3, 1, b"\x00\x27", "fe dc ba c4 f3 00 03 01 00 27 ef"),
            (0xF2, 1, b"\x03\x00\x2f\x01", "fe dc ba c4 f2 00 05 01 03 00 2f 01 ef"),
            (
                0xF2,
                2,
                b"\x05\x00\x02\x02\x05\x04",
                "fe dc ba c4 f2 00 07 02 05 00 02 02 05 04 ef",
            ),
        ]
        for op, seq, value, expected in cases:
            self.assertEqual(encode_request(op, seq, value), bytes.fromhex(expected))

    def test_every_split_and_byte_at_a_time(self):
        for wire in (INFO_FRAME, F4, response(0xF2, 2)):
            expected = StreamParser().feed(wire)
            for split in range(len(wire) + 1):
                parser = StreamParser()
                self.assertEqual(
                    parser.feed(wire[:split]) + parser.feed(wire[split:]), expected
                )
            parser = StreamParser()
            actual = [frame for octet in wire for frame in parser.feed(bytes((octet,)))]
            self.assertEqual(actual, expected)

    def test_concatenation_and_notification_type(self):
        frames = StreamParser().feed(F4 + response(0xF2, 2) + INFO_FRAME)
        self.assertTrue(frames[0].is_request)
        self.assertTrue(frames[0].needs_reply)
        self.assertIsNone(frames[0].status)
        self.assertEqual(frames[1].status, 0)
        self.assertEqual(
            encode_reply(frames[0]), bytes.fromhex("fe dc ba 00 f4 00 02 00 02 ef")
        )

    def test_ef_and_header_inside_payload(self):
        payload = b"\xef\xfe\xdc\xba\xef"
        self.assertEqual(StreamParser().feed(response(2, 1, payload))[0].data, payload)

    def test_resync_after_noise_invalid_lengths_and_footer(self):
        valid = response(2, 5)
        for prefix in (
            b"garbage",
            b"\xfe\xdc\xba\x04\x02\xff\xff",
            b"\xfe\xdc\xba\x04\x02\x00\x00",
            valid[:-1] + b"x",
        ):
            self.assertEqual(
                StreamParser().feed(prefix + valid), StreamParser().feed(valid)
            )

    def test_header_prefix_and_memory_bound(self):
        parser = StreamParser()
        self.assertEqual(parser.feed(b"x" * 100_000 + b"\xfe\xdc"), [])
        self.assertEqual(parser.buffered_bytes, 2)
        self.assertEqual(len(parser.feed(INFO_FRAME[2:])), 1)

    def test_info_and_batteries(self):
        info = decode_info(INFO)
        self.assertEqual((info.vid, info.pid), (0x2717, 0x509B))
        self.assertEqual(info.product_name, "Redmi Buds 6 Play")
        self.assertEqual(info.firmware_raw, "20222022")
        self.assertEqual([b.level for b in info.batteries], [100] * 3)
        self.assertEqual([b.charging for b in info.batteries], [True, True, False])
        for raw in (0, 0x80, 0xFF, 101, 127):
            self.assertIsNone(battery(raw).level)
            self.assertIsNone(battery(raw).charging)
        self.assertEqual(battery(1).level, 1)

    def test_unknown_blocks_and_typed_gestures(self):
        self.assertEqual(decode_info(INFO + b"\x03\x99\x12\x34").pid, 0x509B)
        self.assertEqual(decode_gestures(GESTURES)[3], (0, 9))
        self.assertEqual(decode_gestures(GESTURES[6:] + GESTURES[:6])[4], (5, 9))

    def test_unsupported_configuration_is_explicit(self):
        self.assertIsNone(config_value(bytes.fromhex("04 00 07 ff ff"), 7))
        self.assertEqual(config_value(bytes.fromhex("03 00 07 00"), 7), b"\0")

    def test_invalid_blocks(self):
        for data in (b"\0", b"\x02\x01", b"\x01\x01\x01\x01"):
            with self.assertRaises(ProtocolError):
                decode_blocks(data, 1)
        with self.assertRaises(ProtocolError):
            decode_gestures(b"\x01\x02")
        with self.assertRaises(ProtocolError):
            config_value(bytes.fromhex("03 00 02 01"), 7)
