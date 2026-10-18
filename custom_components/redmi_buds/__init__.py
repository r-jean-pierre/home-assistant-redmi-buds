"""Redmi Buds 6 Play integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_ADDRESS, CONF_CHANNEL, CONF_INTERVAL, DEFAULT_CHANNEL
from .coordinator import BudsCoordinator
from .mma import BudsClient

PLATFORMS = (
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.BUTTON,
)
type BudsConfigEntry = ConfigEntry[BudsCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: BudsConfigEntry) -> bool:
    client = BudsClient(
        entry.data[CONF_ADDRESS], entry.data.get(CONF_CHANNEL, DEFAULT_CHANNEL)
    )
    coordinator = BudsCoordinator(hass, entry, client)
    entry.runtime_data = coordinator
    # Manual mode waits for an explicit refresh before connecting.
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    async def stop(_event) -> None:
        await coordinator.async_stop()

    entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    if entry.options.get(CONF_INTERVAL, 0):
        await coordinator.async_refresh()
    return True


async def _async_options_updated(hass: HomeAssistant, entry: BudsConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: BudsConfigEntry) -> bool:
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.async_stop()
    return unloaded
