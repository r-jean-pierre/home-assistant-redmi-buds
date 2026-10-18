import socket
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor

from mma.client import BudsClient, Session
from mma.protocol import (
    ConnectionError,
    DeviceRejected,
    IncompatibleDevice,
    RequestTimeout,
    WriteUnconfirmed,
)

from .support import ADDRESS, FakeSocket, response


class ClientTests(unittest.TestCase):
    def client(self, sock):
        return BudsClient(ADDRESS, socket_factory=lambda: sock)

    def test_snapshot_and_socket_closed(self):
        sock = FakeSocket()
        data = self.client(sock).read()
        self.assertEqual(data.serial, "TEST-SERIAL-000001")
        self.assertEqual(data.equalizer, 5)
        self.assertTrue(data.latency)
        self.assertEqual(data.gestures[2], (5, 4))
        self.assertEqual(sock.target, (ADDRESS, 6))
        self.assertEqual(sock.connect_timeout, 15)
        self.assertTrue(sock.closed)

    def test_notification_before_ack_not_matching_reply(self):
        sock = FakeSocket()
        client = self.client(sock)
        result = client.set_config(0x2F, 0)
        self.assertFalse(result.latency)
        replies = [f for f in sock.sent if not f.is_request]
        self.assertEqual(len(replies), 1)
        self.assertEqual((replies[0].opcode, replies[0].status), (0xF4, 0))
        self.assertEqual(len([f for f in sock.sent if f.opcode == 0xF2]), 1)

    def test_gesture_read_modify_write_preserves_other_side(self):
        sock = FakeSocket()
        result = self.client(sock).set_gesture(1, 0, 1)
        self.assertEqual(result.gestures[1], (1, 3))
        write = next(f for f in sock.sent if f.opcode == 0xF2)
        self.assertEqual(write.data, bytes.fromhex("05 00 02 01 01 03"))
        self.assertEqual(result.gestures[3], (0, 9))

    def test_disallowed_long_and_tap_actions_are_blocked(self):
        for args in (
            (3, 0, 1),
            (3, 0, 5),
            (1, 0, 0),
            (2, 0, 0),
            (4, 0, 0),
            (5, 0, 1),
            (1, 2, 1),
        ):
            sock = FakeSocket()
            with self.assertRaises(ValueError):
                self.client(sock).set_gesture(*args)
            self.assertEqual(sock.sent, [])

    def test_long_press_writes_use_type_03_and_preserve_the_other_side(self):
        for side in (0, 1):
            for action in (8, 0, 9):
                with self.subTest(side=side, action=action):
                    sock = FakeSocket()
                    expected = [0, 9]
                    expected[side] = action
                    data = self.client(sock).set_gesture(3, side, action)
                    self.assertEqual(data.gestures[3], tuple(expected))
                    write = next(frame for frame in sock.sent if frame.opcode == 0xF2)
                    self.assertEqual(write.data, bytes((5, 0, 2, 3, *expected)))

    def test_new_tap_actions_write_readback_and_preserve_opposite_side(self):
        cases = [(gesture, action) for gesture in (1, 2, 4) for action in (8, 9)]
        cases += [(4, 2), (4, 3)]
        for gesture, action in cases:
            with self.subTest(gesture=gesture, action=action):
                sock = FakeSocket()
                previous = self.client(FakeSocket()).read().gestures[gesture]
                result = self.client(sock).set_gesture(gesture, 0, action)
                self.assertEqual(result.gestures[gesture], (action, previous[1]))
                write = next(frame for frame in sock.sent if frame.opcode == 0xF2)
                self.assertEqual(
                    write.data, bytes((5, 0, 2, gesture, action, previous[1]))
                )

    def test_incompatible_product_blocks_write(self):
        sock = FakeSocket()
        sock.info = sock.info.replace(
            bytes.fromhex("27 17 50 9b"), bytes.fromhex("27 17 50 9c")
        )
        with self.assertRaises(IncompatibleDevice):
            self.client(sock).set_config(7, 0)
        self.assertFalse(any(f.opcode == 0xF2 for f in sock.sent))
        self.assertTrue(sock.closed)

    def test_write_uncertain_and_never_retried(self):
        sock = FakeSocket()
        sock.drop_write = True
        with self.assertRaises(WriteUnconfirmed):
            self.client(sock).set_config(7, 0)
        self.assertEqual(len([f for f in sock.sent if f.opcode == 0xF2]), 1)
        self.assertTrue(sock.closed)

    def test_rejected_write(self):
        sock = FakeSocket()
        sock.reject_write = True
        with self.assertRaises(DeviceRejected):
            self.client(sock).set_config(7, 0)
        self.assertTrue(sock.closed)

    def test_connect_failure_closes_socket(self):
        sock = FakeSocket()
        sock.connect_error = True
        with self.assertRaises(ConnectionError):
            self.client(sock).read()
        self.assertTrue(sock.closed)

    def test_close_is_permanent(self):
        sock = FakeSocket()
        client = self.client(sock)
        client.close()
        with self.assertRaises(ConnectionError):
            client.read()
        self.assertEqual(sock.sent, [])

    def test_close_interrupts_an_active_socket_read(self):
        started, released = threading.Event(), threading.Event()

        class BlockingSocket(FakeSocket):
            def recv(self, size):
                started.set()
                if not released.wait(2):
                    raise AssertionError("Client did not interrupt its socket")
                return b""

            def shutdown(self, how):
                released.set()

            def close(self):
                released.set()
                super().close()

        sock = BlockingSocket()
        client = self.client(sock)
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(client.read)
            try:
                self.assertTrue(started.wait(1))
                client.close()
                with self.assertRaises(ConnectionError):
                    future.result(timeout=1)
                self.assertTrue(sock.closed)
            finally:
                released.set()

    def test_sequence_wraps(self):
        client = self.client(FakeSocket())
        client._sequence = 255
        self.assertEqual(client._next_sequence(), 0)
        self.assertEqual(client._next_sequence(), 1)

    def test_eof_and_wrong_opcode_sequence(self):
        class Incoming(FakeSocket):
            def sendall(self, data):
                self.pending.extend(response(0xF2, 1) + response(2, 2))

        with self.assertRaises(ConnectionError):
            Session(Incoming(), lambda: 1).request(2, b"\xff" * 4)

    def test_timeout_has_global_deadline(self):
        class NoResponse(FakeSocket):
            def sendall(self, data):
                pass

            def recv(self, size):
                raise socket.timeout

        ticks = iter(range(100))
        with self.assertRaises(RequestTimeout):
            Session(NoResponse(), lambda: 1, clock=lambda: next(ticks)).request(
                2, b"\xff" * 4
            )
