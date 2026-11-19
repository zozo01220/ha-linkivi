"""Conditions d'un écran Linkivi (§309), pour l'éditeur d'automatisations : « Appareil » › l'écran › Condition.

L'écran est en ligne, hors ligne, en veille, éveillé, diffuse une liste donnée, ou une alerte d'urgence est en cours. Elles lisent l'état tenu à jour par le canal temps réel.
"""

from __future__ import annotations

import voluptuous as vol

from homeassistant.const import CONF_CONDITION, CONF_DEVICE_ID, CONF_DOMAIN, CONF_TYPE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import selector
from homeassistant.helpers.condition import ConditionCheckerType
from homeassistant.helpers.typing import ConfigType, TemplateVarsType

from .const import DOMAIN

ONLINE, OFFLINE, ASLEEP, AWAKE, PLAYLIST, EMERGENCY = "is_online", "is_offline", "is_asleep", "is_awake", "shows_playlist", "shows_emergency"
CONDITION_TYPES = [ONLINE, OFFLINE, ASLEEP, AWAKE, PLAYLIST, EMERGENCY]

CONDITION_SCHEMA = cv.DEVICE_CONDITION_BASE_SCHEMA.extend(
    {vol.Required(CONF_TYPE): vol.In(CONDITION_TYPES), vol.Optional("playlist"): cv.string}
)


def _screen(hass: HomeAssistant, device_id: str):
    device = dr.async_get(hass).async_get(device_id)
    if device is None:
        return None
    sid = next((i for d, i in device.identifiers if d == DOMAIN and not i.startswith("org_")), None)
    if sid is None:
        return None
    for entry in hass.config_entries.async_entries(DOMAIN):
        coordinator = getattr(entry, "runtime_data", None)
        if coordinator is not None and sid in (coordinator.data or {}):
            return coordinator, sid
    return None


async def async_get_conditions(hass: HomeAssistant, device_id: str) -> list[dict[str, str]]:
    if _screen(hass, device_id) is None:
        return []
    return [{CONF_CONDITION: "device", CONF_DOMAIN: DOMAIN, CONF_DEVICE_ID: device_id, CONF_TYPE: t} for t in CONDITION_TYPES]


async def async_get_condition_capabilities(hass: HomeAssistant, config: ConfigType) -> dict[str, vol.Schema]:
    if config[CONF_TYPE] != PLAYLIST:
        return {}
    found = _screen(hass, config[CONF_DEVICE_ID])
    names = sorted(found[0].playlists.values(), key=str.casefold) if found else []
    return {"extra_fields": vol.Schema({vol.Required("playlist"): selector.SelectSelector(selector.SelectSelectorConfig(options=names, custom_value=True))})}


@callback
def async_condition_from_config(hass: HomeAssistant, config: ConfigType) -> ConditionCheckerType:
    device_id, kind, wanted = config[CONF_DEVICE_ID], config[CONF_TYPE], (config.get("playlist") or "").strip().casefold()

    @callback
    def test(hass: HomeAssistant, variables: TemplateVarsType = None) -> bool:
        found = _screen(hass, device_id)
        if found is None:
            return False
        coordinator, sid = found
        s = coordinator.data.get(sid, {})
        if kind == ONLINE:
            return bool(s.get("online"))
        if kind == OFFLINE:
            return not s.get("online")
        if kind == ASLEEP:
            return bool(s.get("online")) and bool(s.get("asleep"))
        if kind == AWAKE:
            return bool(s.get("online")) and not s.get("asleep")
        if kind == PLAYLIST:
            return ((s.get("playlist") or {}).get("name") or "").casefold() == wanted
        return bool(coordinator.emergencies)   # alerte d'urgence en cours dans l'organisation

    return test
