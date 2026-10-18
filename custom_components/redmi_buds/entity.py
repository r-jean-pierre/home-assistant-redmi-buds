"""Device identity and shared availability."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ADDRESS, DOMAIN, NAME
from .coordinator import BudsCoordinator
from .mma.model import MODEL_IDS, SUPPORTED_PRODUCT


class BudsEntity(CoordinatorEntity[BudsCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: BudsCoordinator, key: str) -> None:
        super().__init__(coordinator)
        address = coordinator.entry.data[CONF_ADDRESS]
        self._attr_unique_id = f"{address}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            name=NAME,
            manufacturer="Xiaomi",
            model=NAME,
            model_id=MODEL_IDS[SUPPORTED_PRODUCT],
        )

    @property
    def available(self) -> bool:
        return (
            not self.coordinator.stopped
            and self.coordinator.last_update_success
            and self.coordinator.data is not None
        )
