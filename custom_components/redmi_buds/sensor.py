"""Batteries, read-only long presses and last observation time."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory

from .entity import BudsEntity
from .mma.model import ACTIONS, label_for

PARALLEL_UPDATES = 0


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [
            *(
                BatterySensor(coordinator, side, i)
                for i, side in enumerate(("left", "right", "case"))
            ),
            *(
                LongPressSensor(coordinator, side, i)
                for i, side in enumerate(("left", "right"))
            ),
            LastReadSensor(coordinator),
            FirmwareSensor(coordinator),
            SerialSensor(coordinator),
        ]
    )


class BatterySensor(BudsEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, side, index) -> None:
        super().__init__(coordinator, f"battery_{side}")
        self.index = index

    @property
    def native_value(self):
        data = self.coordinator.data
        return (
            data.info.batteries[self.index].level
            if data and data.info.batteries
            else None
        )


class LongPressSensor(BudsEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_options = [*ACTIONS, "unrecognized"]

    def __init__(self, coordinator, side, index) -> None:
        super().__init__(coordinator, f"gesture_long_{side}")
        self.index = index

    @property
    def native_value(self):
        data = self.coordinator.data
        if not data or 3 not in data.gestures:
            return None
        value = label_for(ACTIONS, data.gestures[3][self.index])
        return value if value in ACTIONS else "unrecognized"


class LastReadSensor(BudsEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "last_read")

    @property
    def available(self):
        return self.coordinator.last_success is not None

    @property
    def native_value(self):
        return self.coordinator.last_success


class FirmwareSensor(BudsEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator) -> None:
        # Stable key shared by the raw and formatted firmware value.
        super().__init__(coordinator, "firmware_raw")

    @property
    def native_value(self):
        if (data := self.coordinator.data) is None:
            return None
        return data.info.firmware_version or data.info.firmware_raw

    @property
    def extra_state_attributes(self):
        if (data := self.coordinator.data) is None:
            return None
        return {
            "firmware_raw": data.info.firmware_raw,
            "version_source": "observed_signature_mapping"
            if data.info.firmware_version
            else "raw_unknown_signature",
        }


class SerialSensor(BudsEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "serial_number")

    @property
    def native_value(self):
        return self.coordinator.data.serial if self.coordinator.data else None
