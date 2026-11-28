"""Validate settings used to open a Bluetooth RFCOMM connection."""

import re

DEFAULT_CHANNEL = 6
RFCOMM_CHANNELS = range(1, 31)
_MAC_ADDRESS = re.compile(r"(?:[0-9A-F]{2}:){5}[0-9A-F]{2}")


class InvalidAddress(ValueError):
    """The Bluetooth address is not a MAC address."""


class InvalidChannel(ValueError):
    """The RFCOMM channel is not a supported whole number."""


def normalize_address(value: object) -> str:
    if isinstance(value, str):
        address = value.strip().replace("-", ":").upper()
        if _MAC_ADDRESS.fullmatch(address):
            return address
    raise InvalidAddress("Invalid Bluetooth MAC address")


def validate_channel(value: object) -> int:
    if (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value in RFCOMM_CHANNELS
    ):
        return value
    raise InvalidChannel(
        f"RFCOMM channel must be a whole number from {RFCOMM_CHANNELS.start} "
        f"to {RFCOMM_CHANNELS.stop - 1}"
    )
