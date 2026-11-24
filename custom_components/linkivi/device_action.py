"""Actions d'un écran Linkivi (§309), pour l'éditeur d'automatisations : « Appareil » › l'écran › Action.

Afficher un message (en coin, en plein écran ou dans le bandeau, avec l'image d'une caméra), effacer, changer de liste, éteindre ou rallumer l'écran,
redémarrer le player ou l'appareil, déclencher l'alerte d'urgence sur cet écran. Ce sont les mêmes appels que les actions linkivi.* et les entités.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_TYPE
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import selector
from homeassistant.helpers.typing import ConfigType, TemplateVarsType

from .api import LinkivError
from .const import CMD_REBOOT, CMD_RESTART_PLAYER, CMD_SCREEN_OFF, CMD_WAKE, CORNERS, DOMAIN, LOOKS, PLACES, PLACES_SHOWN
from .message import read_image, show

SHOW_MESSAGE, CLEAR, SHOW_LIST, SCREEN_OFF, WAKE, RESTART_PLAYER, REBOOT, EMERGENCY = (
    "show_message", "clear_display", "show_list", "screen_off", "wake", "restart_player", "reboot", "start_emergency",
)
COMMANDS = {SCREEN_OFF: CMD_SCREEN_OFF, WAKE: CMD_WAKE, RESTART_PLAYER: CMD_RESTART_PLAYER, REBOOT: CMD_REBOOT}
ACTION_TYPES = [SHOW_MESSAGE, CLEAR, SHOW_LIST, SCREEN_OFF, WAKE, RESTART_PLAYER, REBOOT, EMERGENCY]

MESSAGE_FIELDS = {
    vol.Optional("title"): vol.All(cv.string, vol.Length(max=60)),
    vol.Optional("message"): vol.All(cv.string, vol.Length(max=300)),
    vol.Optional("place", default="corner"): vol.In(PLACES),
    vol.Optional("corner", default=CORNERS[0]): vol.In(CORNERS),
    vol.Optional("look", default=LOOKS[0]): vol.In(LOOKS),
    vol.Optional("blur", default=False): cv.boolean,
    vol.Optional("duration"): vol.All(vol.Coerce(int), vol.Range(min=5, max=3600)),
    vol.Optional("camera"): cv.entity_id,
    vol.Optional("wake", default=False): cv.boolean,
}

ACTION_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(ACTION_TYPES),
        **MESSAGE_FIELDS,
        vol.Optional("playlist"): cv.string,
        vol.Optional("emergency_title"): vol.All(cv.string, vol.Length(max=40)),
        vol.Optional("emergency_message"): vol.All(cv.string, vol.Length(max=300)),
    }
)


def _screen(hass: HomeAssistant, device_id: str) -> tuple[Any, str] | None:
    """Le coordinateur et l'identifiant Linkivi de l'écran derrière cet appareil (None : appareil « Organisation » ou inconnu)."""
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


async def async_get_actions(hass: HomeAssistant, device_id: str) -> list[dict[str, str]]:
    found = _screen(hass, device_id)
    if found is None:
        return []
    coordinator, sid = found
    supported = set(coordinator.data[sid].get("commands") or [])
    types = [t for t in ACTION_TYPES if t != REBOOT or CMD_REBOOT in supported]   # redémarrer l'appareil : seulement si le matériel le permet
    if "emergency:write" not in coordinator.scopes:
        types.remove(EMERGENCY)
    return [{CONF_DOMAIN: DOMAIN, CONF_DEVICE_ID: device_id, CONF_TYPE: t} for t in types]


async def async_get_action_capabilities(hass: HomeAssistant, config: ConfigType) -> dict[str, vol.Schema]:
    """Champs à remplir dans l'éditeur, selon l'action."""
    t = config[CONF_TYPE]
    if t == SHOW_MESSAGE:
        return {
            "extra_fields": vol.Schema(
                {
                    vol.Optional("title"): selector.TextSelector(),
                    vol.Optional("message"): selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
                    vol.Optional("place", default="corner"): selector.SelectSelector(selector.SelectSelectorConfig(options=PLACES_SHOWN, translation_key="place")),
                    vol.Optional("corner", default=CORNERS[0]): selector.SelectSelector(selector.SelectSelectorConfig(options=CORNERS, translation_key="corner")),
                    vol.Optional("look", default=LOOKS[0]): selector.SelectSelector(selector.SelectSelectorConfig(options=LOOKS, translation_key="look")),
                    vol.Optional("blur", default=False): selector.BooleanSelector(),
                    vol.Optional("duration"): selector.NumberSelector(selector.NumberSelectorConfig(min=5, max=3600, unit_of_measurement="s", mode=selector.NumberSelectorMode.BOX)),
                    vol.Optional("camera"): selector.EntitySelector(selector.EntitySelectorConfig(domain="camera")),
                    vol.Optional("wake", default=False): selector.BooleanSelector(),
                }
            )
        }
    if t == SHOW_LIST:
        found = _screen(hass, config[CONF_DEVICE_ID])
        names = sorted(found[0].playlists.values(), key=str.casefold) if found else []
        return {"extra_fields": vol.Schema({vol.Required("playlist"): selector.SelectSelector(selector.SelectSelectorConfig(options=names, custom_value=True))})}
    if t == EMERGENCY:
        return {
            "extra_fields": vol.Schema(
                {
                    vol.Required("emergency_title"): selector.TextSelector(),
                    vol.Optional("emergency_message"): selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
                }
            )
        }
    return {}


async def async_call_action_from_config(hass: HomeAssistant, config: ConfigType, variables: TemplateVarsType, context: Context | None) -> None:
    found = _screen(hass, config[CONF_DEVICE_ID])
    if found is None:
        raise HomeAssistantError("Cet écran Linkivi n'est plus connu.")
    coordinator, sid = found
    api = coordinator.api
    t = config[CONF_TYPE]
    try:
        if t == SHOW_MESSAGE:
            if not config.get("title") and not config.get("message"):
                raise HomeAssistantError("Indiquez un titre ou un message.")
            data = {k: config.get(k) for k in ("title", "message", "place", "corner", "look", "blur", "duration", "camera", "wake")}
            await show(hass, api, sid, data, await read_image(hass, config.get("camera"), None))
        elif t == CLEAR:
            await api.clear_display(sid)
        elif t == SHOW_LIST:
            name = (config.get("playlist") or "").strip()
            pid = name if name in coordinator.playlists else next((i for i, n in coordinator.playlists.items() if n.casefold() == name.casefold()), None)
            if pid is None:
                raise HomeAssistantError(f"Liste « {name} » introuvable dans Linkivi.")
            await api.set_playlist(sid, pid)
        elif t == EMERGENCY:
            await api.start_emergency(config["emergency_title"], config.get("emergency_message"), [sid], "Home Assistant")
        else:
            await api.command(sid, COMMANDS[t])
    except LinkivError as err:
        raise HomeAssistantError(f"{coordinator.data.get(sid, {}).get('name', 'Écran')} : {err}") from err
    await coordinator.async_request_refresh()
