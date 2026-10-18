"""A refresh button remains available while the earbuds are asleep."""

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.exceptions import HomeAssistantError

from .entity import BudsEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    async_add_entities([RefreshButton(entry.runtime_data)])


class RefreshButton(BudsEntity, ButtonEntity):
    _attr_device_class = ButtonDeviceClass.UPDATE

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "refresh")

    @property
    def available(self):
        return not self.coordinator.stopped

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()
        if not self.coordinator.last_update_success:
            raise HomeAssistantError(
                "Cannot refresh the earbuds; wake them and check the Bluetooth connection"
            )
