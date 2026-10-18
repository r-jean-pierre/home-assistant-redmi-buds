"""Read paired BlueZ identities without connecting, scanning or pairing devices."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass


class DiscoveryUnavailable(Exception):
    """Local BlueZ objects could not be read."""


@dataclass(frozen=True)
class PairedDevice:
    address: str
    name: str
    likely_model: bool


def parse_paired_devices(objects: dict) -> list[PairedDevice]:
    """List candidates by name; model verification happens during connection."""
    found: dict[str, PairedDevice] = {}
    for interfaces in objects.values():
        if not isinstance(interfaces, dict):
            continue
        props = interfaces.get("org.bluez.Device1", {})
        if not isinstance(props, dict) or props.get("Paired") is not True:
            continue
        if props.get("Blocked") or props.get("AddressType", "public") != "public":
            continue
        address = props.get("Address")
        if not isinstance(address, str):
            continue
        address = address.upper()
        if not re.fullmatch(r"(?:[0-9A-F]{2}:){5}[0-9A-F]{2}", address):
            continue
        name = props.get("Name", "")
        alias = props.get("Alias", "")
        name = name if isinstance(name, str) else ""
        alias = alias if isinstance(alias, str) else ""
        likely = any("redmi buds 6 play" in value.casefold() for value in (name, alias))
        device = PairedDevice(
            address, (alias.strip() or name.strip() or "Bluetooth")[:128], likely
        )
        # One public identity can be paired on several local adapters.
        if address not in found or (likely and not found[address].likely_model):
            found[address] = device
    return sorted(
        found.values(),
        key=lambda item: (not item.likely_model, item.name.casefold(), item.address),
    )


async def async_list_paired_devices() -> list[PairedDevice]:
    """Use the BlueZ helper supplied by HA's native Bluetooth dependency."""
    try:
        from bluetooth_adapters.dbus import get_dbus_managed_objects

        # The upstream helper unpacks D-Bus variants and closes its own bus.
        async with asyncio.timeout(5):
            objects = await get_dbus_managed_objects()
    except (
        ImportError,
        OSError,
        TimeoutError,
        EOFError,
        TypeError,
        AttributeError,
    ) as err:
        raise DiscoveryUnavailable(
            "Cannot read local paired Bluetooth devices"
        ) from err
    return parse_paired_devices(objects)
