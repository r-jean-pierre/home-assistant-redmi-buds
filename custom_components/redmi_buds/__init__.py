"""Redmi Buds 6 Play integration."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

from .const import CONF_ADDRESS, CONF_CHANNEL, CONF_INTERVAL, DEFAULT_CHANNEL
from .mma import BudsClient

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .coordinator import BudsConfigEntry

PLATFORMS = ("sensor", "binary_sensor", "switch", "select", "button")


async def async_setup_entry(hass: HomeAssistant, entry: BudsConfigEntry) -> bool:
    from homeassistant.const import EVENT_HOMEASSISTANT_STOP

    # The protocol can be imported without Home Assistant.
    coordinator_module = await hass.async_add_import_executor_job(
        import_module, f"{__name__}.coordinator"
    )
    client = BudsClient(
        entry.data[CONF_ADDRESS], entry.data.get(CONF_CHANNEL, DEFAULT_CHANNEL)
    )
    coordinator = coordinator_module.BudsCoordinator(hass, entry, client)
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
