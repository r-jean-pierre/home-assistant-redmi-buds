"""Redmi Buds 6 Play data models and decoders."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .protocol import IncompatibleDevice, ProtocolError, decode_blocks

SUPPORTED_PRODUCT = (0x2717, 0x509B)
# Model reference by product identifier.
MODEL_IDS = {SUPPORTED_PRODUCT: "M2420E1"}
# Firmware versions by product and raw signature; unknown signatures remain raw.
KNOWN_FIRMWARE = {(0x2717, 0x509B, "20222022"): "2.0.2.2"}
CONFIG_GESTURES = 0x0002
CONFIG_EQ = 0x0007
CONFIG_SERIAL = 0x0027
CONFIG_LATENCY = 0x002F
EQ_PROFILES = {"balanced": 0, "voice": 1, "bass": 5, "treble": 6, "volume": 7}
ACTIONS = {
    "voice_assistant": 0,
    "play_pause": 1,
    "previous_track": 2,
    "next_track": 3,
    "volume_up": 4,
    "volume_down": 5,
    "none": 8,
    "take_photo": 9,
}
GESTURES = {"single": 4, "double": 1, "triple": 2, "long": 3}
# Available actions for each gesture type.
WRITABLE_ACTIONS = {
    4: (1, 2, 3, 4, 5, 8, 9),
    1: (1, 2, 3, 4, 5, 8, 9),
    2: (1, 2, 3, 4, 5, 8, 9),
    3: (8, 0, 9),
}


@dataclass(frozen=True)
class Battery:
    raw: int
    level: int | None
    charging: bool | None


def battery(raw: int) -> Battery:
    level = raw & 0x7F
    valid = 1 <= level <= 100
    return Battery(raw, level if valid else None, bool(raw & 0x80) if valid else None)


@dataclass(frozen=True)
class DeviceInfo:
    product_name: str | None
    vid: int
    pid: int
    firmware_raw: str | None
    batteries: tuple[Battery, Battery, Battery] | None

    @property
    def model_id(self) -> str | None:
        return MODEL_IDS.get((self.vid, self.pid))

    @property
    def firmware_version(self) -> str | None:
        return KNOWN_FIRMWARE.get((self.vid, self.pid, self.firmware_raw))


def decode_info(data: bytes) -> DeviceInfo:
    blocks = decode_blocks(data, 1)
    product = blocks.get(3)
    if product is None or len(product) != 4:
        raise IncompatibleDevice("Missing compatible product identifier")
    vid, pid = int.from_bytes(product[:2], "big"), int.from_bytes(product[2:], "big")
    if (vid, pid) != SUPPORTED_PRODUCT:
        raise IncompatibleDevice("Only Redmi Buds 6 Play are supported")
    cells = blocks.get(7)
    if cells is not None and len(cells) != 3:
        raise ProtocolError("Invalid battery block length")
    name = blocks.get(0)
    return DeviceInfo(
        name.decode("utf-8", errors="replace") if name else None,
        vid,
        pid,
        blocks[1].hex() if 1 in blocks else None,
        tuple(battery(raw) for raw in cells) if cells is not None else None,
    )


def config_value(data: bytes, config_id: int) -> bytes | None:
    blocks = decode_blocks(data, 2)
    if config_id not in blocks:
        raise ProtocolError("Response is missing the requested configuration")
    value = blocks[config_id]
    if not value:
        raise ProtocolError("Empty configuration value")
    return None if all(octet == 0xFF for octet in value) else value


def decode_gestures(value: bytes | None) -> dict[int, tuple[int, int]]:
    if value is None:
        return {}
    if len(value) % 3:
        raise ProtocolError("Invalid gesture triplet length")
    result = {}
    for offset in range(0, len(value), 3):
        gesture, left, right = value[offset : offset + 3]
        if gesture in result:
            raise ProtocolError("Duplicate gesture type")
        result[gesture] = (left, right)
    return result


def decode_byte(value: bytes | None) -> int | None:
    if value is None:
        return None
    if len(value) != 1:
        raise ProtocolError("Expected a one-byte configuration")
    return value[0]


def decode_serial(value: bytes | None) -> str | None:
    if value is None:
        return None
    try:
        return value.rstrip(b"\x00").decode("ascii")
    except UnicodeDecodeError as err:
        raise ProtocolError("Invalid serial number encoding") from err


@dataclass(frozen=True)
class Snapshot:
    info: DeviceInfo
    serial: str | None
    latency: bool | None
    equalizer: int | None
    gestures: dict[int, tuple[int, int]]
    observed_at: datetime


def label_for(mapping: dict[str, int], value: int | None) -> str | None:
    if value is None:
        return None
    return next(
        (key for key, number in mapping.items() if number == value), f"code_{value:02x}"
    )
