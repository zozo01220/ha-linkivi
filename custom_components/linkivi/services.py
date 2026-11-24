"""Actions Linkivi : afficher un message sur des écrans, et le retirer."""

from __future__ import annotations

import asyncio
import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .api import LinkivError
from .message import read_image, show
from .const import (
    DOMAIN,
    CORNERS,
    LOOKS,
    PLACES,
    SERVICE_CLEAR_DISPLAY,
    SERVICE_END_EMERGENCY,
    SERVICE_SHOW_COUNTDOWN,
    SERVICE_SHOW_LIST,
    SERVICE_SHOW_MESSAGE,
    SERVICE_START_EMERGENCY,
)

_LOGGER = logging.getLogger(__name__)

# Les clés de cible (entity_id, device_id, area_id, floor_id, label_id) passent telles quelles (extra=ALLOW_EXTRA) : on les lit nous-mêmes,
# sans dépendre d'une fonction interne de Home Assistant qui change d'une version à l'autre.
SHOW_MESSAGE_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Optional("title"): vol.All(cv.string, vol.Length(max=60)),
            vol.Optional("message"): vol.All(cv.string, vol.Length(max=300)),
            vol.Optional("look", default=LOOKS[0]): vol.In(LOOKS),
            vol.Optional("blur", default=False): cv.boolean,   # plein écran sur fond flouté : la diffusion reste visible derrière (§316)
            vol.Optional("duration"): vol.All(vol.Coerce(int), vol.Range(min=5, max=3600)),   # sans durée : 30 s, 15 s en coin (Linkivi)
            vol.Optional("wake", default=False): cv.boolean,
            vol.Optional("place", default="full"): vol.In(PLACES),
            vol.Optional("corner", default=CORNERS[0]): vol.In(CORNERS),
            vol.Optional("camera"): cv.entity_id,
            vol.Optional("image_url"): cv.url,
            vol.Optional("live", default=False): cv.boolean,
            vol.Optional("tag"): vol.All(cv.string, vol.Length(max=40)),
            # compte à rebours (§344) : toujours accepté ici pour les automatisations d'avant la 1.15, mais masqué dans l'éditeur ;
            # l'action show_countdown (§347) le remplace
            vol.Optional("countdown_to"): cv.datetime,
            vol.Optional("paused", default=False): cv.boolean,
            vol.Optional("more", default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=9)),
            vol.Optional("ended_message"): vol.All(cv.string, vol.Length(max=300)),
        },
        extra=vol.ALLOW_EXTRA,
    ),
    cv.has_at_least_one_key("title", "message"),
)

# Compte à rebours (§347) : action à part pour ne plus mêler ses champs à ceux d'un message ; même envoi à Linkivi que show_message.
COUNTDOWN_TAG = "countdown"   # étiquette par défaut : « Arrêter l'affichage » avec cette étiquette retire le compte à rebours seul
SHOW_COUNTDOWN_SCHEMA = vol.Schema(
    {
        vol.Required("ends_at"): cv.datetime,
        vol.Optional("title"): vol.All(cv.string, vol.Length(max=60)),
        vol.Optional("message"): vol.All(cv.string, vol.Length(max=300)),
        vol.Optional("paused", default=False): cv.boolean,
        vol.Optional("others", default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=9)),
        vol.Optional("ended_message"): vol.All(cv.string, vol.Length(max=300)),
        vol.Optional("place", default="banner_top"): vol.In(PLACES),
        vol.Optional("corner", default=CORNERS[0]): vol.In(CORNERS),
        vol.Optional("wake", default=False): cv.boolean,
        vol.Optional("tag", default=COUNTDOWN_TAG): vol.All(cv.string, vol.Length(max=40)),
    },
    extra=vol.ALLOW_EXTRA,
)


def countdown_data(data: dict) -> dict:
    """Champs de show_countdown → champs de l'envoi d'un message (message.show)."""
    title = data.get("title")
    if not title and not data.get("message"):
        title = "Minuteur"   # Linkivi veut un titre ou un message
    return {
        "title": title,
        "message": data.get("message"),
        "place": data.get("place") or "banner_top",
        "corner": data.get("corner"),
        "wake": data.get("wake"),
        "tag": (data.get("tag") or "").strip() or COUNTDOWN_TAG,
        "countdown_to": data["ends_at"],
        "paused": data.get("paused"),
        "more": data.get("others") or 0,
        "ended_message": data.get("ended_message"),
    }


CLEAR_DISPLAY_SCHEMA = vol.Schema({vol.Optional("tag"): vol.All(cv.string, vol.Length(max=40))}, extra=vol.ALLOW_EXTRA)

SHOW_LIST_SCHEMA = vol.Schema({vol.Required("playlist"): cv.string}, extra=vol.ALLOW_EXTRA)

START_EMERGENCY_SCHEMA = vol.Schema(
    {vol.Required("title"): vol.All(cv.string, vol.Length(max=40)), vol.Optional("message"): vol.All(cv.string, vol.Length(max=300))},
    extra=vol.ALLOW_EXTRA,
)


def _ids(call: ServiceCall, key: str) -> set[str]:
    value = call.data.get(key)
    if value is None:
        return set()
    return {v for v in ([value] if isinstance(value, str) else list(value)) if isinstance(v, str) and v not in ("none", "all")}


async def _screens_of(hass: HomeAssistant, call: ServiceCall) -> list[tuple[object, str]]:
    """Les écrans Linkivi visés par l'action (écrans, appareils, pièces, étages, libellés), avec le coordinateur qui les connaît."""
    entity_reg = er.async_get(hass)
    device_reg = dr.async_get(hass)
    area_reg = ar.async_get(hass)

    entity_ids = _ids(call, "entity_id")
    device_ids = _ids(call, "device_id")
    area_ids = _ids(call, "area_id")
    labels = _ids(call, "label_id")
    floors = _ids(call, "floor_id")
    if floors:
        area_ids |= {a.id for a in area_reg.async_list_areas() if a.floor_id in floors}
    if labels:
        entity_ids |= {e.entity_id for e in entity_reg.entities.values() if labels & set(e.labels)}
        device_ids |= {d.id for d in device_reg.devices.values() if labels & set(d.labels)}
    for area_id in area_ids:   # une pièce : ses appareils, et les entités rangées directement dedans
        device_ids |= {d.id for d in dr.async_entries_for_area(device_reg, area_id)}
        entity_ids |= {e.entity_id for e in er.async_entries_for_area(entity_reg, area_id)}

    screen_ids: set[str] = set()
    for entity_id in entity_ids:
        entry = entity_reg.async_get(entity_id)
        if entry and entry.platform == DOMAIN and entry.unique_id:
            screen_ids.add(entry.unique_id.split("_", 1)[0])   # « {écran}_{entité} »
    for device_id in device_ids:
        device = device_reg.async_get(device_id)
        if device:
            screen_ids.update(ident for domain, ident in device.identifiers if domain == DOMAIN)

    found: list[tuple[object, str]] = []
    for entry in hass.config_entries.async_entries(DOMAIN):
        coordinator = getattr(entry, "runtime_data", None)
        if coordinator is None:
            continue
        found.extend((coordinator, sid) for sid in sorted(screen_ids) if sid in coordinator.data)
    if not found:
        raise ServiceValidationError("Choisissez au moins un écran Linkivi (un écran, un appareil ou une pièce).")
    return found


def _has_target(call: ServiceCall) -> bool:
    return any(_ids(call, k) for k in ("entity_id", "device_id", "area_id", "floor_id", "label_id"))


async def _run(call: ServiceCall, send) -> None:
    """Envoie à chaque écran ; une erreur d'un écran n'empêche pas les autres, et toutes sont rapportées ensemble."""
    targets = await _screens_of(call.hass, call)

    async def one(coordinator, screen_id: str) -> str | None:
        name = coordinator.data.get(screen_id, {}).get("name", screen_id)
        try:
            await send(coordinator.api, screen_id)
        except LinkivError as err:
            return f"{name} : {err}"
        return None

    # tous les écrans en même temps : un minuteur qui s'arrête ne doit pas attendre les allers-retours de chaque écran, l'un après l'autre
    results = await asyncio.gather(*(one(c, s) for c, s in targets), return_exceptions=True)
    failures: list[str] = []
    for res in results:
        if isinstance(res, BaseException):
            raise res
        if res:
            failures.append(res)
    if failures:
        raise HomeAssistantError("\n".join(failures))


async def async_register_services(hass: HomeAssistant) -> None:
    """Déclare les actions ; appelé une fois, au chargement de l'intégration."""

    async def show_message(call: ServiceCall) -> None:
        data = dict(call.data)
        image = await read_image(hass, data.get("camera"), data.get("image_url"))   # lue une fois, envoyée à chaque écran

        async def send(api, screen_id: str) -> None:
            await show(hass, api, screen_id, data, image)

        await _run(call, send)

    async def show_countdown(call: ServiceCall) -> None:
        data = countdown_data(dict(call.data))

        async def send(api, screen_id: str) -> None:
            await show(hass, api, screen_id, data, None)

        await _run(call, send)

    async def clear_display(call: ServiceCall) -> None:
        tag = (call.data.get("tag") or "").strip() or None   # seulement les messages de cette étiquette (ex. le minuteur, §344)

        async def send(api, screen_id: str) -> None:
            await api.clear_display(screen_id, tag=tag)

        await _run(call, send)

    async def show_list(call: ServiceCall) -> None:
        name = call.data["playlist"].strip()

        async def send(api, screen_id: str) -> None:
            coordinator = next(e.runtime_data for e in hass.config_entries.async_entries(DOMAIN) if getattr(e, "runtime_data", None) and e.runtime_data.api is api)
            pid = name if name in coordinator.playlists else next((i for i, n in coordinator.playlists.items() if n.casefold() == name.casefold()), None)
            if pid is None:
                raise LinkivError(f"liste « {name} » introuvable")
            await api.set_playlist(screen_id, pid)

        await _run(call, send)

    async def start_emergency(call: ServiceCall) -> None:
        """Déclenche une urgence sur les écrans visés (ou sur tous, sans cible)."""
        data = call.data
        targeted = _has_target(call)
        groups: dict[object, list[str]] = {}
        if targeted:
            for coordinator, sid in await _screens_of(hass, call):
                groups.setdefault(coordinator, []).append(sid)
        else:
            groups = {e.runtime_data: [] for e in hass.config_entries.async_entries(DOMAIN) if getattr(e, "runtime_data", None)}
        failures = []
        for coordinator, ids in groups.items():
            if "emergency:write" not in coordinator.scopes:
                failures.append(f"{coordinator.org_name} : cette autorisation date d'avant l'urgence pour tous. Dans Paramètres › Appareils et services › Linkivi, menu ⋮ › « Reconfigurer » (intégration 1.7.2 ou plus) : une nouvelle autorisation par code ajoute l'urgence.")
                continue
            try:
                await coordinator.api.start_emergency(data["title"], data.get("message"), ids, "Home Assistant")
            except LinkivError as err:
                failures.append(f"{coordinator.org_name} : {err}")
        if failures:
            raise HomeAssistantError("\n".join(failures))

    async def end_emergency(call: ServiceCall) -> None:
        """Lève toutes les urgences en cours (de toutes les organisations reliées)."""
        failures = []
        for e in hass.config_entries.async_entries(DOMAIN):
            coordinator = getattr(e, "runtime_data", None)
            if coordinator is None or "emergency:write" not in coordinator.scopes:
                continue
            try:
                for em in await coordinator.api.emergencies():
                    await coordinator.api.end_emergency(em["id"])
            except LinkivError as err:
                failures.append(f"{coordinator.org_name} : {err}")
        if failures:
            raise HomeAssistantError("\n".join(failures))

    hass.services.async_register(DOMAIN, SERVICE_SHOW_LIST, show_list, schema=SHOW_LIST_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_START_EMERGENCY, start_emergency, schema=START_EMERGENCY_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_END_EMERGENCY, end_emergency, schema=vol.Schema({}))
    hass.services.async_register(DOMAIN, SERVICE_SHOW_MESSAGE, show_message, schema=SHOW_MESSAGE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SHOW_COUNTDOWN, show_countdown, schema=SHOW_COUNTDOWN_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_CLEAR_DISPLAY, clear_display, schema=CLEAR_DISPLAY_SCHEMA)
