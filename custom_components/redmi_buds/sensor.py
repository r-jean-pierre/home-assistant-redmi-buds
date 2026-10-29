"""Battery levels, device information and last successful read."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.helpers import entity_registry as er

from .const import CONF_ADDRESS, DOMAIN
from .entity import BudsEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = entry.runtime_data
    registry = er.async_get(hass)
    removed_unique_ids = {
        f"{entry.data[CONF_ADDRESS]}_gesture_long_{side}" for side in ("left", "right")
    }
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if (
            entity.domain == "sensor"
            and entity.platform == DOMAIN
            and entity.unique_id in removed_unique_ids
        ):
            registry.async_remove(entity.entity_id)

    async_add_entities(
        [
            *(
                BatterySensor(coordinator, side, i)
                for i, side in enumerate(("left", "right", "case"))
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
