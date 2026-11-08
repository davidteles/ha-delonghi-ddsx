"""Mode: Dehumidify / Purify only / Off. The unit does one job at a time."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DDSXConfigEntry
from .const import DEHUM_ACTIVE, PURIFIER_ACTIVE
from .entity import DDSXEntity

DEHUMIDIFY, PURIFY, OFF = "dehumidify", "purify", "off"


async def async_setup_entry(hass: HomeAssistant, entry: DDSXConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    c = entry.runtime_data
    if DEHUM_ACTIVE in c.chars and PURIFIER_ACTIVE in c.chars:
        async_add_entities([DDSXMode(c, DEHUM_ACTIVE, "mode")])


class DDSXMode(DDSXEntity, SelectEntity):
    _attr_options = [DEHUMIDIFY, PURIFY, OFF]

    @property
    def current_option(self) -> str | None:
        data = self.coordinator.data or {}
        if data.get(DEHUM_ACTIVE):
            return DEHUMIDIFY
        if data.get(PURIFIER_ACTIVE):
            return PURIFY
        return OFF if DEHUM_ACTIVE in data else None

    async def async_select_option(self, option: str) -> None:
        # Switching the purifier off turns the whole unit off, so to change mode we
        # only ever switch the wanted job on; the unit stops the other one itself.
        if option == DEHUMIDIFY:
            await self.coordinator.async_write({DEHUM_ACTIVE: 1})
        elif option == PURIFY:
            await self.coordinator.async_write({PURIFIER_ACTIVE: 1})
        else:
            await self.coordinator.async_write({DEHUM_ACTIVE: 0, PURIFIER_ACTIVE: 0})
