"""Partager avec Linkivi (§303, lot 3) : les écrans montrent les appareils choisis ici, sans qu'aucun jeton Home Assistant soit gardé chez Linkivi.

Linkivi envoie ses demandes par le canal temps réel (« ha.request » : états, commandes, historique, image de caméra, aires) ;
l'intégration y répond dans Home Assistant (« ha.reply »), seulement pour les entités partagées, et prévient Linkivi quand l'une d'elles change
(« ha.changed ») ou quand le partage change (« ha.share »).
"""

from __future__ import annotations

import base64
import json
import logging
from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, unquote, urlsplit

from homeassistant.const import EVENT_STATE_CHANGED
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.json import JSONEncoder
from homeassistant.util import dt as dt_util

if TYPE_CHECKING:
    from . import LinkivCoordinator

_LOGGER = logging.getLogger(__name__)

# Options de l'entrée (Paramètres › Appareils et services › Linkivi › Configurer)
OPT_AREAS = "share_areas"
OPT_LABELS = "share_labels"
OPT_ENTITIES = "share_entities"
OPT_COMMANDS = "share_commands"

# Serrures et alarmes : jamais par une pièce ou un libellé, seulement choisies une à une (décision 5 de la maquette)
SENSITIVE = ("lock", "alarm_control_panel")

# Entité apparue ou disparue : le partage est revu au bout de ce délai (s), une fois pour toutes celles arrivées entre-temps
RESHARE_DELAY = 5


def _dumps(obj: Any) -> str:
    return json.dumps(obj, cls=JSONEncoder, ensure_ascii=False)


def _int(value: str | None) -> int | None:
    """Taille d'image demandée (16 à 3840 px), ou None."""
    try:
        n = int(value) if value else 0
    except ValueError:
        return None
    return n if 16 <= n <= 3840 else None


class LinkivShare:
    """Le partage d'une entrée : quelles entités, commandes permises ou non, et les réponses aux demandes de Linkivi."""

    def __init__(self, hass: HomeAssistant, coordinator: LinkivCoordinator) -> None:
        self.hass = hass
        self.coordinator = coordinator
        self.entities: set[str] = set()
        self._last_changed = 0.0
        self._unsub = None
        # Entités partagées qui avaient un état au dernier partage envoyé : Linkivi ne connaît que celles-là (1.10.1)
        self._announced: frozenset[str] = frozenset()
        self._reshare_unsub = None

    @property
    def options(self) -> dict[str, Any]:
        return dict(self.coordinator.config_entry.options)

    @property
    def commands(self) -> bool:
        return bool(self.options.get(OPT_COMMANDS, False))

    def compute(self) -> set[str]:
        """Entités partagées : celles des pièces et libellés choisis (sans serrures ni alarmes), plus celles choisies une à une."""
        o = self.options
        areas = set(o.get(OPT_AREAS) or [])
        labels = set(o.get(OPT_LABELS) or [])
        chosen = set(o.get(OPT_ENTITIES) or [])
        ent_reg = er.async_get(self.hass)
        dev_reg = dr.async_get(self.hass)
        result = set(chosen)
        for e in ent_reg.entities.values():
            if e.disabled or e.entity_id.split(".", 1)[0] in SENSITIVE:
                continue
            device = dev_reg.async_get(e.device_id) if e.device_id else None
            area = e.area_id or (device.area_id if device else None)
            if area in areas or labels & set(e.labels) or (device and labels & set(device.labels)):
                result.add(e.entity_id)
        self.entities = {i for i in result if self.hass.states.get(i) is not None or i in chosen}
        return self.entities

    def _stated(self) -> frozenset[str]:
        """Entités partagées qui ont un état : Linkivi relit la liste par les états, les autres lui restent inconnues."""
        return frozenset(i for i in self.entities if self.hass.states.get(i) is not None)

    def share_message(self) -> dict[str, Any]:
        self.compute()
        self._announced = self._stated()
        return {
            "type": "ha.share", "name": self.hass.config.location_name or "Home Assistant", "entities": sorted(self.entities), "commands": self.commands,
            # adresses de Home Assistant (1.10.0) : les écrans de la maison y lisent eux-mêmes l'image des caméras partagées, sans passer par Linkivi
            "internal": self._url(internal=True), "external": self._url(internal=False),
        }

    def _url(self, internal: bool) -> str:
        from homeassistant.helpers.network import NoURLAvailableError, get_url   # noqa: PLC0415

        try:
            if internal:
                return get_url(self.hass, allow_internal=True, allow_external=False, allow_cloud=False, allow_ip=True, prefer_external=False)
            return get_url(self.hass, allow_internal=False, allow_external=True, allow_cloud=True, allow_ip=False, require_ssl=True, prefer_external=True)
        except NoURLAvailableError:
            return ""

    @callback
    def watch(self, send) -> None:
        """Prévient Linkivi quand une entité partagée change (au plus une fois par seconde : Linkivi relit alors les états)."""
        if self._unsub:
            self._unsub()

        @callback
        def _reshare(_now: Any) -> None:
            """Une entité est apparue ou a disparu : le partage est renvoyé s'il a changé (Linkivi relit alors la liste)."""
            self._reshare_unsub = None
            before = self._announced
            message = self.share_message()
            if self._announced != before:
                self.hass.async_create_task(send(message))

        @callback
        def _changed(event: Event) -> None:
            # Au démarrage de Home Assistant, les intégrations lentes (cloud, voitures…) publient leurs états après le premier partage :
            # sans ce renvoi, Linkivi garderait une liste incomplète jusqu'à sa relecture du jour (1.10.1).
            if (event.data.get("old_state") is None) != (event.data.get("new_state") is None) and self._reshare_unsub is None:
                self._reshare_unsub = async_call_later(self.hass, RESHARE_DELAY, _reshare)
            if event.data.get("entity_id") not in self.entities:
                return
            now = self.hass.loop.time()
            if now - self._last_changed < 1:
                return
            self._last_changed = now
            self.hass.async_create_task(send({"type": "ha.changed"}))

        self._unsub = self.hass.bus.async_listen(EVENT_STATE_CHANGED, _changed)

    def stop(self) -> None:
        if self._reshare_unsub:
            self._reshare_unsub()
            self._reshare_unsub = None
        if self._unsub:
            self._unsub()
            self._unsub = None

    # ---------- réponses aux demandes de Linkivi ----------

    async def answer(self, req: dict[str, Any]) -> dict[str, Any] | None:
        """Réponse à une « ha.request » (None : demande pour une autre clé, ou périmée)."""
        if req.get("key") and self.coordinator.key_id and req.get("key") != self.coordinator.key_id:
            return None
        expires = dt_util.parse_datetime(req.get("expires") or "")
        if expires and expires < dt_util.utcnow():
            return None
        reply: dict[str, Any] = {"type": "ha.reply", "id": req.get("id")}
        try:
            status, body, ctype, binary = await self._route(req.get("method", "GET"), req.get("path", ""), req.get("body"))
        except Exception as err:  # noqa: BLE001 — Linkivi reçoit l'erreur comme une réponse 500, jamais un plantage du canal
            _LOGGER.warning("Linkivi : demande %s %s en échec : %s", req.get("method"), req.get("path"), err)
            status, body, ctype, binary = 500, _dumps({"message": str(err)}), "application/json", False
        reply["status"] = status
        if binary:
            reply["body64"] = base64.b64encode(body).decode()
        else:
            reply["body"] = body
        if ctype:
            reply["contentType"] = ctype
        return reply

    async def _route(self, method: str, path: str, body: str | None) -> tuple[int, Any, str | None, bool]:
        self.compute()
        parts = urlsplit(path)
        p = parts.path
        if method == "GET" and p == "/api/states":
            states = [s.as_dict() for s in self.hass.states.async_all() if s.entity_id in self.entities]
            return 200, _dumps(states), "application/json", False
        if method == "GET" and p.startswith("/api/states/"):
            eid = unquote(p[len("/api/states/"):])
            s = self.hass.states.get(eid) if eid in self.entities else None
            return (200, _dumps(s.as_dict()), "application/json", False) if s else (404, "{}", "application/json", False)
        if method == "POST" and p.startswith("/api/services/"):
            return await self._service(p, body)
        if method == "GET" and p.startswith("/api/camera_proxy/"):
            eid = unquote(p[len("/api/camera_proxy/"):])
            if eid not in self.entities or not eid.startswith("camera."):
                return 404, b"", None, True
            from homeassistant.components.camera import async_get_image   # noqa: PLC0415 — seulement si une caméra est partagée

            # taille affichée par l'écran (1.10.0) : Home Assistant réduit l'image (jamais au-delà de sa taille d'origine)
            q = parse_qs(parts.query)
            width = _int(q.get("width", [None])[0])
            height = _int(q.get("height", [None])[0])
            img = await async_get_image(self.hass, eid, width=width, height=height)
            return 200, img.content, img.content_type, True
        if method == "GET" and p.startswith("/api/media_player_proxy/"):
            # pochette d'un lecteur partagé (application « En cours de lecture », 1.9.0) : celle que Home Assistant sert à son propre tableau de bord
            eid = unquote(p[len("/api/media_player_proxy/"):])
            if eid not in self.entities or not eid.startswith("media_player."):
                return 404, b"", None, True
            component = self.hass.data.get("media_player")
            entity = component.get_entity(eid) if component is not None else None
            if entity is None:
                return 404, b"", None, True
            data, ctype = await entity.async_get_media_image()
            if not data:
                return 404, b"", None, True
            return 200, data, ctype or "image/jpeg", True
        if method == "GET" and p.startswith("/api/history/period/"):
            return await self._history(p, parts.query)
        if method == "POST" and p == "/api/template":
            # aires de Home Assistant pour « Importer les aires » de l'écran Home Assistant (§297) : le résultat ne cite que des entités partagées
            text = await self._areas_template((json.loads(body or "{}") or {}).get("template", ""))
            return 200, text, "text/plain", False
        return 404, _dumps({"message": "Non partagé par l'intégration Linkivi."}), "application/json", False

    async def _service(self, p: str, body: str | None) -> tuple[int, Any, str | None, bool]:
        if not self.commands:
            return 403, _dumps({"message": "Les écrans n'ont pas le droit de commander ces appareils (options de l'intégration Linkivi)."}), "application/json", False
        domain, _, service = p[len("/api/services/"):].partition("/")
        data = json.loads(body or "{}") or {}
        ids = data.get("entity_id")
        ids = [ids] if isinstance(ids, str) else list(ids or [])
        if not ids or any(i not in self.entities for i in ids):
            return 403, _dumps({"message": "Appareil non partagé avec Linkivi."}), "application/json", False
        await self.hass.services.async_call(domain, service, data, blocking=True)
        return 200, "[]", "application/json", False

    async def _history(self, p: str, query: str) -> tuple[int, Any, str | None, bool]:
        from homeassistant.components.recorder import get_instance, history   # noqa: PLC0415

        q = parse_qs(query, keep_blank_values=True)
        start = dt_util.parse_datetime(unquote(p[len("/api/history/period/"):]))
        end = dt_util.parse_datetime((q.get("end_time") or [""])[0]) if q.get("end_time") else None
        ids = [i for i in (q.get("filter_entity_id") or [""])[0].split(",") if i in self.entities]
        if not start or not ids:
            return 200, "[]", "application/json", False
        found = await get_instance(self.hass).async_add_executor_job(
            partial(history.get_significant_states, self.hass, start, end, ids, None, True, False, False, True)
        )
        out = []
        for eid, items in found.items():
            series = []
            for s in items:
                d = s if isinstance(s, dict) else s.as_dict()
                changed = d.get("last_changed")
                series.append({"entity_id": eid, "state": d.get("state"), "last_changed": changed.isoformat() if isinstance(changed, datetime) else changed})
            out.append(series)
        return 200, _dumps(out), "application/json", False

    async def _areas_template(self, template: str) -> str:
        """Aires et leurs entités partagées (le modèle envoyé par Linkivi n'est pas exécuté : seule sa réponse est reproduite)."""
        area_reg = ar.async_get(self.hass)
        ent_reg = er.async_get(self.hass)
        dev_reg = dr.async_get(self.hass)
        rows: dict[str, list[str]] = {}
        for eid in sorted(self.entities):
            e = ent_reg.async_get(eid)
            device = dev_reg.async_get(e.device_id) if e and e.device_id else None
            area_id = (e.area_id if e else None) or (device.area_id if device else None)
            area = area_reg.async_get_area(area_id) if area_id else None
            if area:
                rows.setdefault(area.name, []).append(eid)
        # même forme que le modèle de Linkivi ([{"a": aire, "e": entités}]), mais calculée ici : aucun modèle n'est exécuté dans Home Assistant
        return _dumps([{"a": name, "e": ids} for name, ids in rows.items()])
