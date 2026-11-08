"""Base entity. Entities attach to the unit's existing HomeKit Controller device."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DDSXCoordinator


class DDSXEntity(CoordinatorEntity[DDSXCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: DDSXCoordinator, key: str, translation_key: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{coordinator.hk_entry_id}_{translation_key}"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # Home Assistant gives each device a single config entry, so instead of a
        # second "twin" device the entities are moved onto HomeKit Controller's one.
        device_id = self.coordinator.device_id
        if device_id and self.registry_entry and self.registry_entry.device_id != device_id:
            er.async_get(self.hass).async_update_entity(self.entity_id, device_id=device_id)

    @property
    def raw(self) -> Any:
        return (self.coordinator.data or {}).get(self._key)

    @property
    def available(self) -> bool:
        return super().available and self._key in self.coordinator.chars and self.raw is not None
