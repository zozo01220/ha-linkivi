"""L'écran répond-il à Linkivi ?"""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

from .entity import LinkivEntity, add_new_screens


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    entry.async_on_unload(
        add_new_screens(coordinator, async_add_entities, lambda sid, _s: [LinkivOnlineSensor(coordinator, sid)])
    )
    if "emergency:read" in coordinator.scopes:
        async_add_entities([LinkivEmergencySensor(coordinator)])


class LinkivOnlineSensor(LinkivEntity, BinarySensorEntity):
    """En ligne : l'écran a donné de ses nouvelles ces 90 dernières secondes."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_translation_key = "online"

    def __init__(self, coordinator, screen_id: str) -> None:
        super().__init__(coordinator, screen_id, "online")

    @property
    def is_on(self) -> bool:
        return bool(self.screen.get("online"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        s = self.screen
        return {
            "status": s.get("status"),
            "last_seen": s.get("lastSeenAt"),
            "paused": s.get("paused"),
            "asleep": s.get("asleep"),
            "area": (s.get("area") or {}).get("name"),
            "zone": (s.get("zone") or {}).get("name"),
            "playlist": (s.get("playlist") or {}).get("name"),
            "resolution": s.get("resolution"),
        }


class LinkivEmergencySensor(CoordinatorEntity, BinarySensorEntity):
    """Urgence en cours dans l'organisation (§301) : sur un appareil « Linkivi » à part, en temps réel par le canal."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.SAFETY
    _attr_translation_key = "emergency"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.org_id}_emergency"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"org_{coordinator.org_id}")}, name=coordinator.org_name, manufacturer="Linkivi", model="Organisation",
            configuration_url=coordinator.api.base_url,
        )

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.emergencies)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"emergencies": [{"id": i, "title": t} for i, t in self.coordinator.emergencies.items()]}
