"""Setup: pick a De'Longhi DDSX that is already paired in HomeKit Controller."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import device_registry as dr

from .const import CONF_HK_ENTRY, DOMAIN


class DDSXConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        configured = {entry.data.get(CONF_HK_ENTRY) for entry in self._async_current_entries()}
        dev_reg = dr.async_get(self.hass)
        units: dict[str, str] = {}
        for entry in self.hass.config_entries.async_entries("homekit_controller"):
            if entry.entry_id in configured:
                continue
            for device in dr.async_entries_for_config_entry(dev_reg, entry.entry_id):
                if (device.manufacturer or "").lower().replace("'", "").startswith("delonghi") and (device.model or "").upper().startswith("DDSX"):
                    units[entry.entry_id] = device.name_by_user or device.name or entry.title
                    break
        if not units:
            return self.async_abort(reason="no_device")
        if user_input is not None or len(units) == 1:
            hk_entry_id = user_input[CONF_HK_ENTRY] if user_input else next(iter(units))
            await self.async_set_unique_id(hk_entry_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=f"{units[hk_entry_id]} extras", data={CONF_HK_ENTRY: hk_entry_id})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({vol.Required(CONF_HK_ENTRY): vol.In(units)}))
