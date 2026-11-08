"""Alarm code, current mode, Real Feel colour, mould prediction and resources."""
from __future__ import annotations

import base64

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DDSXConfigEntry
from .const import ALARMS, CURRENT_MODE, MODE_NAMES, MOLD, REAL_FEEL, REAL_FEEL_COLOR, RESOURCES
from .entity import DDSXEntity


def _decode(value) -> bytes:
    try:
        return base64.b64decode(value) if value else b""
    except (ValueError, TypeError):
        return b""


async def async_setup_entry(hass: HomeAssistant, entry: DDSXConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    c = entry.runtime_data
    entities = [
        DDSXAlarmCode(c, ALARMS, "alarm_code"),
        DDSXCurrentMode(c, CURRENT_MODE, "current_mode"),
        DDSXRawNumber(c, REAL_FEEL_COLOR, "real_feel_colour"),
        DDSXRawNumber(c, RESOURCES, "resources", EntityCategory.DIAGNOSTIC),
        DDSXRawData(c, MOLD, "mould_prediction", EntityCategory.DIAGNOSTIC),
    ]
    async_add_entities(e for e in entities if e._key in c.chars)


class DDSXRawNumber(DDSXEntity, SensorEntity):
    def __init__(self, coordinator, key, translation_key, category: EntityCategory | None = None) -> None:
        super().__init__(coordinator, key, translation_key)
        self._attr_entity_category = category

    @property
    def native_value(self):
        return None if self.raw is None else int(self.raw)

    @property
    def extra_state_attributes(self):
        if self._key == REAL_FEEL_COLOR:
            return {"real_feel_bytes": list(_decode((self.coordinator.data or {}).get(REAL_FEEL)))}
        return None


class DDSXAlarmCode(DDSXRawNumber):
    @property
    def extra_state_attributes(self):
        value = self.raw
        if value is None:
            return None
        return {"bits_set": [bit for bit in range(8) if int(value) >> bit & 1], "water_tank": int(value) == 3}


class DDSXCurrentMode(DDSXEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["dehumidify", "purify", "unknown"]
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        return None if self.raw is None else MODE_NAMES.get(int(self.raw), "unknown")

    @property
    def extra_state_attributes(self):
        return {"raw": self.raw}


class DDSXRawData(DDSXEntity, SensorEntity):
    def __init__(self, coordinator, key, translation_key, category: EntityCategory | None = None) -> None:
        super().__init__(coordinator, key, translation_key)
        self._attr_entity_category = category

    @property
    def native_value(self):
        data = _decode(self.raw)
        return data.hex() if data else "0"

    @property
    def extra_state_attributes(self):
        return {"bytes": list(_decode(self.raw))}
