"""Model-specific EQ and gesture settings; retain the opposite side explicitly."""

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.exceptions import HomeAssistantError

from .entity import BudsEntity
from .mma.model import (
    ACTIONS,
    CONFIG_EQ,
    EQ_PROFILES,
    GESTURES,
    WRITABLE_ACTIONS,
    label_for,
)

PARALLEL_UPDATES = 0


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [
            EqualizerSelect(coordinator),
            *(
                GestureSelect(coordinator, gesture, side, i)
                for gesture in ("single", "double", "triple", "long")
                for i, side in enumerate(("left", "right"))
            ),
        ]
    )


class EqualizerSelect(BudsEntity, SelectEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "equalizer")

    @property
    def available(self):
        return super().available and self.coordinator.data.equalizer is not None

    @property
    def current_option(self):
        return (
            label_for(EQ_PROFILES, self.coordinator.data.equalizer)
            if self.coordinator.data
            else None
        )

    @property
    def options(self):
        options = list(EQ_PROFILES)
        if (current := self.current_option) and current not in options:
            options.append(current)
        return options

    async def async_select_option(self, option: str) -> None:
        if option not in EQ_PROFILES:
            raise HomeAssistantError("This EQ value is read-only")
        snapshot = await self.coordinator.async_write(
            "set_config", CONFIG_EQ, EQ_PROFILES[option]
        )
        if snapshot.equalizer != EQ_PROFILES[option]:
            raise HomeAssistantError(
                "The readback differs from the requested equalizer"
            )


class GestureSelect(BudsEntity, SelectEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, gesture, side, index) -> None:
        super().__init__(coordinator, f"gesture_{gesture}_{side}")
        self.gesture = GESTURES[gesture]
        self.index = index

    @property
    def available(self):
        return super().available and self.gesture in self.coordinator.data.gestures

    @property
    def current_option(self):
        data = self.coordinator.data
        return (
            label_for(ACTIONS, data.gestures[self.gesture][self.index])
            if data and self.gesture in data.gestures
            else None
        )

    @property
    def options(self):
        options = [
            label_for(ACTIONS, value) for value in WRITABLE_ACTIONS[self.gesture]
        ]
        if (current := self.current_option) and current not in options:
            options.append(current)
        return options

    async def async_select_option(self, option: str) -> None:
        if (
            option not in ACTIONS
            or ACTIONS[option] not in WRITABLE_ACTIONS[self.gesture]
        ):
            raise HomeAssistantError("This gesture action is read-only")
        snapshot = await self.coordinator.async_write(
            "set_gesture", self.gesture, self.index, ACTIONS[option]
        )
        if (
            snapshot.gestures.get(self.gesture, (None, None))[self.index]
            != ACTIONS[option]
        ):
            raise HomeAssistantError("The readback differs from the requested gesture")
