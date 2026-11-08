"""Eco mode, Laundry mode, Real Feel and louver swing."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DDSXConfigEntry
from .const import DEHUM_SWING, ECO, LAUNDRY, REAL_FEEL_ON
from .entity import DDSXEntity

SWITCHES = [  # key, translation key, written as 0/1 instead of a boolean
    (ECO, "eco_mode", False),
    (LAUNDRY, "laundry_mode", False),
    (REAL_FEEL_ON, "real_feel", True),
    (DEHUM_SWING, "louver_swing", True),
]


async def async_setup_entry(hass: HomeAssistant, entry: DDSXConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    c = entry.runtime_data
    async_add_entities(DDSXSwitch(c, key, tkey, as_int) for key, tkey, as_int in SWITCHES if key in c.chars)


class DDSXSwitch(DDSXEntity, SwitchEntity):
    def __init__(self, coordinator, key: str, translation_key: str, as_int: bool) -> None:
        super().__init__(coordinator, key, translation_key)
        self._as_int = as_int

    @property
    def is_on(self) -> bool | None:
        return None if self.raw is None else bool(self.raw)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_write({self._key: 1 if self._as_int else True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_write({self._key: 0 if self._as_int else False})
