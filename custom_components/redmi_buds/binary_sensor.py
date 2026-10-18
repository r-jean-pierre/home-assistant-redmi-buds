"""Charging flags are unknown when their associated level is invalid."""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)

from .entity import BudsEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    async_add_entities(
        ChargingSensor(entry.runtime_data, side, i)
        for i, side in enumerate(("left", "right", "case"))
    )


class ChargingSensor(BudsEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    def __init__(self, coordinator, side, index) -> None:
        super().__init__(coordinator, f"charging_{side}")
        self.index = index

    @property
    def is_on(self):
        data = self.coordinator.data
        return (
            data.info.batteries[self.index].charging
            if data and data.info.batteries
            else None
        )

    @property
    def icon(self):
        if self.is_on is None:
            return "mdi:battery-unknown"
        return "mdi:battery-charging" if self.is_on else "mdi:battery"
