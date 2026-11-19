"""État d'un écran et dernière connexion (§301), en capteurs à part (avant : attributs de « En ligne »)."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .entity import LinkivEntity, add_new_screens

STATES = ["online", "offline", "updating", "asleep", "paused"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    entry.async_on_unload(
        add_new_screens(coordinator, async_add_entities, lambda sid, s: [LinkivStateSensor(coordinator, sid), LinkivLastSeenSensor(coordinator, sid)] + ([LinkivBatterySensor(coordinator, sid)] if s.get("battery") else []))
    )


class LinkivStateSensor(LinkivEntity, SensorEntity):
    """En ligne, hors ligne, mise à jour en cours, en veille ou en pause."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = STATES
    _attr_translation_key = "state"

    def __init__(self, coordinator, screen_id: str) -> None:
        super().__init__(coordinator, screen_id, "state")

    @property
    def native_value(self) -> str | None:
        s = self.screen
        if not s:
            return None
        if s.get("status") == "offline":
            return "offline"
        if s.get("asleep"):
            return "asleep"
        if s.get("paused"):
            return "paused"
        return "updating" if s.get("status") == "updating" else "online"


class LinkivLastSeenSensor(LinkivEntity, SensorEntity):
    """Dernière fois que l'écran a donné de ses nouvelles."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_translation_key = "last_seen"
    _attr_entity_registry_enabled_default = False   # change toutes les quelques secondes : à activer si besoin

    def __init__(self, coordinator, screen_id: str) -> None:
        super().__init__(coordinator, screen_id, "last_seen")

    @property
    def native_value(self) -> datetime | None:
        raw = self.screen.get("lastSeenAt")
        return dt_util.parse_datetime(raw) if raw else None


class LinkivBatterySensor(LinkivEntity, SensorEntity):
    """Batterie d'un smartphone ou d'une tablette Android (§309) : dernier niveau connu. Pour la recharger entre 20 et 80 % par une prise connectée."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, screen_id: str) -> None:
        super().__init__(coordinator, screen_id, "battery")

    @property
    def native_value(self) -> int | None:
        b = self.screen.get("battery")
        return b.get("level") if b else None
