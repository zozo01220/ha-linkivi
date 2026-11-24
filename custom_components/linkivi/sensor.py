"""État d'un écran et dernière connexion (§301), en capteurs à part (avant : attributs de « En ligne ») ; dernier démarrage et version du player (§349) ;
santé de l'appareil (§350) : température, disque, mémoire, Wi-Fi, sur tous les écrans (« Inconnu » quand le player ne la mesure pas)."""

from __future__ import annotations

from datetime import datetime

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT, EntityCategory, UnitOfTemperature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .entity import LinkivEntity, add_new_screens

STATES = ["online", "offline", "updating", "asleep", "paused"]


def _disk_used(h: dict) -> float | None:
    free, total = h.get("diskFreeMb"), h.get("diskTotalMb")
    return round(100 * (total - free) / total, 1) if free is not None and total else None


def _disk_attrs(h: dict) -> dict:
    free, total = h.get("diskFreeMb"), h.get("diskTotalMb")
    return {"free_gb": round(free / 1024, 1), "total_gb": round(total / 1024, 1)} if free is not None and total else {}


# Santé de l'appareil (§350) : clé, valeur lue dans « health », attributs
HEALTH: tuple[tuple[SensorEntityDescription, Any, Any], ...] = (
    (SensorEntityDescription(key="cpu_temperature", translation_key="cpu_temperature", device_class=SensorDeviceClass.TEMPERATURE,
                             native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT), lambda h: h.get("cpuTemperature"), None),
    (SensorEntityDescription(key="disk_used", translation_key="disk_used", icon="mdi:harddisk", native_unit_of_measurement=PERCENTAGE,
                             state_class=SensorStateClass.MEASUREMENT), _disk_used, _disk_attrs),
    (SensorEntityDescription(key="memory_used", translation_key="memory_used", icon="mdi:memory", native_unit_of_measurement=PERCENTAGE,
                             state_class=SensorStateClass.MEASUREMENT), lambda h: h.get("memoryUsedPercent"), None),
    (SensorEntityDescription(key="wifi_signal", translation_key="wifi_signal", device_class=SensorDeviceClass.SIGNAL_STRENGTH,
                             native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT, state_class=SensorStateClass.MEASUREMENT), lambda h: h.get("wifiDbm"), None),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    entry.async_on_unload(
        add_new_screens(coordinator, async_add_entities, lambda sid, s: [LinkivStateSensor(coordinator, sid), LinkivLastSeenSensor(coordinator, sid), LinkivBootSensor(coordinator, sid), LinkivVersionSensor(coordinator, sid)]
            + [LinkivHealthSensor(coordinator, sid, d) for d in HEALTH] + ([LinkivBatterySensor(coordinator, sid)] if s.get("battery") else []))
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


class LinkivBootSensor(LinkivEntity, SensorEntity):
    """Dernier démarrage de l'appareil (§349), tel que le player l'a remonté : un redémarrage inattendu se voit ici."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "booted_at"

    def __init__(self, coordinator, screen_id: str) -> None:
        super().__init__(coordinator, screen_id, "booted_at")

    @property
    def native_value(self) -> datetime | None:
        raw = self.screen.get("bootedAt")
        return dt_util.parse_datetime(raw) if raw else None


class LinkivVersionSensor(LinkivEntity, SensorEntity):
    """Version de l'application Linkivi Player (§349) ; aussi sur la fiche de l'appareil (« Micrologiciel »). Attributs : système et modèle."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "player_version"

    def __init__(self, coordinator, screen_id: str) -> None:
        super().__init__(coordinator, screen_id, "player_version")

    @property
    def native_value(self) -> str | None:
        return self.screen.get("playerVersion")

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        return {k: v for k, v in (("os", self.screen.get("os")), ("model", self.screen.get("model"))) if v}


class LinkivHealthSensor(LinkivEntity, SensorEntity):
    """Une mesure de santé de l'appareil (§350), remontée par le player toutes les 5 min ; « Inconnu » si ce player ne la mesure pas."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, screen_id: str, health: tuple) -> None:
        description, self._read, self._attrs = health
        super().__init__(coordinator, screen_id, description.key)
        self.entity_description = description

    @property
    def native_value(self):
        h = self.screen.get("health")
        return self._read(h) if h else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        h = self.screen.get("health")
        return self._attrs(h) if h and self._attrs else None
