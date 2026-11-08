"""De'Longhi DDSX extras.

Adds the private De'Longhi features (eco, laundry, mode, louver swing, alarms,
real feel, mould prediction) that Home Assistant's HomeKit Controller ignores.
It reuses HomeKit Controller's existing local pairing; it never pairs again and
never talks to the cloud.
"""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ACTIVE, ALARMS, CONF_HK_ENTRY, CURRENT_MODE, DEHUM_ACTIVE, DEHUM_SWING, DEHUMIDIFIER_SERVICE, DOMAIN, ECO,
    LAUNDRY, MOLD, PRIVATE_SERVICE, PURIFIER_ACTIVE, PURIFIER_SERVICE, REAL_FEEL, REAL_FEEL_COLOR, REAL_FEEL_ON,
    RESOURCES, SCAN_SECONDS, SWING,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.BINARY_SENSOR, Platform.SELECT, Platform.SENSOR, Platform.SWITCH]
PRIVATE_KEYS = [LAUNDRY, ECO, MOLD, REAL_FEEL_ON, CURRENT_MODE, REAL_FEEL, REAL_FEEL_COLOR, ALARMS, RESOURCES]

type DDSXConfigEntry = ConfigEntry["DDSXCoordinator"]


def find_connection(hass: HomeAssistant, hk_entry_id: str) -> Any | None:
    """Return HomeKit Controller's live connection for the unit, if it is loaded."""
    entry = hass.config_entries.async_get_entry(hk_entry_id)
    if entry is None:
        return None
    conn = getattr(entry, "runtime_data", None)
    if conn is not None and hasattr(conn, "pairing"):
        return conn
    for value in list(hass.data.values()):  # older Home Assistant versions
        if isinstance(value, dict):
            for candidate in list(value.values()):
                if hasattr(candidate, "pairing") and getattr(getattr(candidate, "config_entry", None), "entry_id", None) == hk_entry_id:
                    return candidate
    return None


def _short(uuid: Any) -> str:
    return str(uuid).replace("-", "").upper()[:8]


def map_characteristics(conn: Any) -> dict[str, tuple[int, int]]:
    """Find (aid, iid) for every characteristic we use, by UUID."""
    found: dict[str, tuple[int, int]] = {}
    for accessory in conn.entity_map.accessories:
        for service in accessory.services:
            stype = _short(service.type)
            for char in service.characteristics:
                ctype = _short(char.type)
                key = None
                if stype == PRIVATE_SERVICE and ctype in PRIVATE_KEYS:
                    key = ctype
                elif stype == DEHUMIDIFIER_SERVICE and ctype == ACTIVE:
                    key = DEHUM_ACTIVE
                elif stype == DEHUMIDIFIER_SERVICE and ctype == SWING:
                    key = DEHUM_SWING
                elif stype == PURIFIER_SERVICE and ctype == ACTIVE:
                    key = PURIFIER_ACTIVE
                if key and key not in found:
                    found[key] = (accessory.aid, char.iid)
    return found


class DDSXCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls the unit and writes changes back."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, hk_entry_id: str, chars: dict[str, tuple[int, int]]) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=SCAN_SECONDS), config_entry=entry)
        self.hk_entry_id = hk_entry_id
        self.chars = chars
        self.device_id: str | None = None
        dev_reg = dr.async_get(hass)
        aids = {aid for aid, _ in chars.values()}
        for device in dr.async_entries_for_config_entry(dev_reg, hk_entry_id):
            if any(str(ident[1]).endswith(f":aid:{aid}") for ident in device.identifiers for aid in aids):
                self.device_id = device.id
                break

    def _conn(self) -> Any:
        conn = find_connection(self.hass, self.hk_entry_id)
        if conn is None:
            raise UpdateFailed("The HomeKit connection to the unit is not ready")
        return conn

    async def _async_update_data(self) -> dict[str, Any]:
        conn = self._conn()
        by_address = {address: key for key, address in self.chars.items()}
        try:
            result = await conn.pairing.get_characteristics(list(by_address))
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Reading the unit failed: {err}") from err
        return {by_address[address]: value["value"] for address, value in result.items() if address in by_address and isinstance(value, dict) and "value" in value}

    async def async_write(self, values: dict[str, Any]) -> None:
        conn = find_connection(self.hass, self.hk_entry_id)
        if conn is None:
            raise HomeAssistantError("The unit is not connected")
        writes = [(*self.chars[key], value) for key, value in values.items() if key in self.chars]
        try:
            await conn.pairing.put_characteristics(writes)
        except Exception as err:  # noqa: BLE001
            raise HomeAssistantError(f"Writing to the unit failed: {err}") from err
        # Show the new value straight away; the next poll confirms it.
        self.async_set_updated_data({**(self.data or {}), **values})


async def async_setup_entry(hass: HomeAssistant, entry: DDSXConfigEntry) -> bool:
    hk_entry_id = entry.data[CONF_HK_ENTRY]
    conn = find_connection(hass, hk_entry_id)
    if conn is None:
        raise ConfigEntryNotReady("Waiting for HomeKit Controller to connect to the unit")
    chars = map_characteristics(conn)
    if ALARMS not in chars:
        raise ConfigEntryNotReady("The De'Longhi private HomeKit service was not found on this unit")
    coordinator = DDSXCoordinator(hass, entry, hk_entry_id, chars)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: DDSXConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
