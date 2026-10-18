"""Shared reads and writes, always outside Home Assistant's asyncio loop."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_ADDRESS, CONF_INTERVAL, DOMAIN
from .mma import BudsClient, BudsError, Snapshot

_LOGGER = logging.getLogger(__name__)


class BudsCoordinator(DataUpdateCoordinator[Snapshot | None]):
    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client: BudsClient
    ) -> None:
        minutes = entry.options.get(CONF_INTERVAL, 0)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=minutes) if minutes else None,
        )
        self.client = client
        self.entry = entry
        self.data = None
        self.last_update_success = False
        self.last_success = None
        self.stopped = False
        self._io_lock = asyncio.Lock()

    async def _async_update_data(self) -> Snapshot:
        async with self._io_lock:
            if self.stopped:
                raise UpdateFailed("Integration is stopped")
            try:
                snapshot = await self.hass.async_add_executor_job(self.client.read)
            except BudsError as err:
                raise UpdateFailed(str(err)) from err
            self.last_success = snapshot.observed_at
            self._update_device_metadata(snapshot)
            return snapshot

    def _update_device_metadata(self, snapshot: Snapshot) -> None:
        registry = dr.async_get(self.hass)
        device = registry.async_get_device_by_identifier(
            (DOMAIN, self.entry.data[CONF_ADDRESS]), self.entry.entry_id
        )
        if device is not None:
            registry.async_update_device(
                device.id,
                model_id=snapshot.info.model_id,
                # Clear an old recognized version if a new signature is unknown.
                sw_version=snapshot.info.firmware_version,
            )

    async def async_write(self, method: str, *args) -> Snapshot:
        async with self._io_lock:
            if self.stopped:
                raise HomeAssistantError("Integration is stopped")
            try:
                snapshot = await self.hass.async_add_executor_job(
                    getattr(self.client, method), *args
                )
            except (BudsError, ValueError) as err:
                self.async_set_update_error(UpdateFailed(str(err)))
                raise HomeAssistantError(str(err)) from err
            self.last_success = snapshot.observed_at
            self._update_device_metadata(snapshot)
            self.async_set_updated_data(snapshot)
            return snapshot

    async def async_stop(self) -> None:
        if self.stopped:
            return
        self.stopped = True
        await self.async_shutdown()
        await self.hass.async_add_executor_job(self.client.close)
        # Wait for any executor operation to unwind before completing unload.
        async with self._io_lock:
            pass
