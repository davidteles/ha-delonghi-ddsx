"""Water tank (alarm code 3) and a general alarm flag."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DDSXConfigEntry
from .const import ALARMS, TANK_ALARM_CODE
from .entity import DDSXEntity


async def async_setup_entry(hass: HomeAssistant, entry: DDSXConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    c = entry.runtime_data
    if ALARMS in c.chars:
        async_add_entities([DDSXAlarm(c, ALARMS, "alarm"), DDSXTank(c, ALARMS, "water_tank")])


class DDSXAlarm(DDSXEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def is_on(self) -> bool | None:
        return None if self.raw is None else int(self.raw) != 0


class DDSXTank(DDSXEntity, BinarySensorEntity):
    """On when the tank is full or not in place (the unit stops drying)."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def is_on(self) -> bool | None:
        return None if self.raw is None else int(self.raw) == TANK_ALARM_CODE
