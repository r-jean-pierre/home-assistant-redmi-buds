"""Bounded, synchronous RFCOMM transactions; callers must use an executor."""

from __future__ import annotations

import secrets
import socket
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime

from .model import (
    CONFIG_EQ,
    CONFIG_GESTURES,
    CONFIG_LATENCY,
    CONFIG_SERIAL,
    EQ_PROFILES,
    WRITABLE_ACTIONS,
    Snapshot,
    config_value,
    decode_byte,
    decode_gestures,
    decode_info,
    decode_serial,
)
from .protocol import (
    GET_CONFIG,
    GET_INFO,
    NOTIFY_CONFIG,
    NOTIFY_INFO,
    SET_CONFIG,
    BudsError,
    ConnectionError,
    DeviceRejected,
    ProtocolError,
    RequestTimeout,
    StreamParser,
    UnsupportedTransport,
    WriteUnconfirmed,
    config_payload,
    encode_reply,
    encode_request,
)


def rfcomm_socket() -> socket.socket:
    if not all(hasattr(socket, field) for field in ("AF_BLUETOOTH", "BTPROTO_RFCOMM")):
        raise UnsupportedTransport("Bluetooth RFCOMM is unavailable on this platform")
    return socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)


class Session:
    def __init__(
        self, sock, next_sequence: Callable[[], int], *, clock=time.monotonic
    ) -> None:
        self.socket = sock
        self._next_sequence = next_sequence
        self._clock = clock
        self._expires = clock() + 30
        self._parser = StreamParser()

    def request(self, opcode: int, payload: bytes) -> bytes:
        sequence = self._next_sequence()
        deadline = min(self._expires, self._clock() + 5)
        remaining = deadline - self._clock()
        if remaining <= 0:
            raise RequestTimeout("MMA session deadline elapsed")
        self.socket.settimeout(remaining)
        self.socket.sendall(encode_request(opcode, sequence, payload))
        while True:
            remaining = deadline - self._clock()
            if remaining <= 0:
                raise RequestTimeout("MMA response deadline elapsed")
            self.socket.settimeout(min(1, remaining))
            try:
                chunk = self.socket.recv(4096)
            except socket.timeout:
                continue
            if not chunk:
                raise ConnectionError("RFCOMM stream closed before a matching response")
            matched = None
            for frame in self._parser.feed(chunk):
                if frame.is_request:
                    # Notifications can share the sequence number of the pending request.
                    if frame.needs_reply:
                        status = (
                            0 if frame.opcode in (NOTIFY_CONFIG, NOTIFY_INFO) else 0xFF
                        )
                        self.socket.settimeout(
                            max(0.001, min(1, deadline - self._clock()))
                        )
                        self.socket.sendall(encode_reply(frame, status))
                    continue
                if frame.opcode == opcode and frame.sequence == sequence:
                    matched = frame
            if matched is not None:
                if matched.status != 0:
                    raise DeviceRejected("Earbuds rejected the MMA command")
                return matched.data

    def get_config(self, config_id: int) -> bytes | None:
        return config_value(
            self.request(GET_CONFIG, config_id.to_bytes(2, "big")), config_id
        )


class BudsClient:
    """One socket per operation; serialize even if an awaiting task is cancelled."""

    def __init__(
        self, address: str, channel: int = 6, *, socket_factory=rfcomm_socket
    ) -> None:
        self.address = address
        self.channel = channel
        self._socket_factory = socket_factory
        self._sequence = secrets.randbelow(256)
        self._operation_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._closed = threading.Event()
        self._active = None

    def _next_sequence(self) -> int:
        self._sequence = (self._sequence + 1) % 256
        return self._sequence

    @contextmanager
    def _session(self) -> Iterator[Session]:
        with self._operation_lock:
            with self._state_lock:
                if self._closed.is_set():
                    raise ConnectionError("RFCOMM client is stopped")
                try:
                    sock = self._socket_factory()
                except OSError as err:
                    raise ConnectionError(
                        "Cannot create the local RFCOMM socket"
                    ) from err
                self._active = sock
            try:
                sock.settimeout(15)
                sock.connect((self.address, self.channel))
                yield Session(sock, self._next_sequence)
            except OSError as err:
                raise ConnectionError("Bluetooth RFCOMM operation failed") from err
            finally:
                with self._state_lock:
                    self._active = None
                sock.close()

    def close(self) -> None:
        """Permanently stop this client and interrupt an active bounded session."""
        with self._state_lock:
            self._closed.set()
            if self._active is not None:
                try:
                    self._active.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                self._active.close()

    def probe(self):
        with self._session() as session:
            return decode_info(session.request(GET_INFO, b"\xff" * 4))

    def _read_all(self, session: Session) -> Snapshot:
        info = decode_info(session.request(GET_INFO, b"\xff" * 4))
        serial = decode_serial(session.get_config(CONFIG_SERIAL))
        latency = decode_byte(session.get_config(CONFIG_LATENCY))
        if latency not in (None, 0, 1):
            raise ProtocolError("Unrecognized low-latency state")
        equalizer = decode_byte(session.get_config(CONFIG_EQ))
        gestures = decode_gestures(session.get_config(CONFIG_GESTURES))
        return Snapshot(
            info,
            serial,
            None if latency is None else bool(latency),
            equalizer,
            gestures,
            datetime.now(UTC),
        )

    def read(self) -> Snapshot:
        with self._session() as session:
            return self._read_all(session)

    def _write_read(self, session: Session, config_id: int, value: bytes) -> Snapshot:
        try:
            session.request(SET_CONFIG, config_payload(config_id, value))
            # Includes all gestures, since single/long settings can be coupled.
            return self._read_all(session)
        except DeviceRejected:
            raise
        except (BudsError, OSError) as err:
            raise WriteUnconfirmed(
                "Write may have applied; refresh before trying again"
            ) from err

    def set_config(self, config_id: int, value: int) -> Snapshot:
        allowed = (
            (0, 1)
            if config_id == CONFIG_LATENCY
            else tuple(EQ_PROFILES.values())
            if config_id == CONFIG_EQ
            else ()
        )
        if value not in allowed:
            raise ValueError("This configuration write is not supported")
        with self._session() as session:
            decode_info(session.request(GET_INFO, b"\xff" * 4))
            return self._write_read(session, config_id, bytes((value,)))

    def set_gesture(self, gesture: int, side: int, action: int) -> Snapshot:
        if side not in (0, 1) or action not in WRITABLE_ACTIONS.get(gesture, ()):
            raise ValueError("This gesture write is not supported")
        with self._session() as session:
            decode_info(session.request(GET_INFO, b"\xff" * 4))
            gestures = decode_gestures(session.get_config(CONFIG_GESTURES))
            if gesture not in gestures:
                raise ProtocolError("Requested gesture is not reported by this device")
            values = list(gestures[gesture])
            # Do not re-send an unknown opposite-side action, especially 0xFF.
            if values[1 - side] not in (0, 1, 2, 3, 4, 5, 8, 9):
                raise ProtocolError("Cannot safely preserve the opposite-side gesture")
            values[side] = action
            return self._write_read(session, CONFIG_GESTURES, bytes((gesture, *values)))
