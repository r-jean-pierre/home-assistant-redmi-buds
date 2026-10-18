"""Low-latency switch."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.exceptions import HomeAssistantError

from .entity import BudsEntity
from .mma.model import CONFIG_LATENCY

PARALLEL_UPDATES = 0


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    async_add_entities([LatencySwitch(entry.runtime_data)])


class LatencySwitch(BudsEntity, SwitchEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "low_latency")

    @property
    def available(self):
        return super().available and self.coordinator.data.latency is not None

    @property
    def is_on(self):
        return self.coordinator.data.latency if self.coordinator.data else None

    async def _set(self, enabled: bool) -> None:
        snapshot = await self.coordinator.async_write(
            "set_config", CONFIG_LATENCY, int(enabled)
        )
        if snapshot.latency != enabled:
            raise HomeAssistantError(
                "The readback differs from the requested low-latency setting"
            )

    async def async_turn_on(self, **kwargs) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._set(False)
