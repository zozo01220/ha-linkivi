"""Canal temps réel de Linkivi (§299) : la connexion part de Home Assistant, Linkivi y pousse l'état des écrans et ses événements.

WebSocket d'abord (wss://…/api/v1/stream) ; si un proxy le bloque (3 échecs de suite), attente longue en HTTPS (GET /stream/next)
pendant 5 minutes, puis nouvel essai du WebSocket. Après une coupure, la reprise se fait au dernier numéro reçu (« seq ») : rien n'est perdu.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any

import aiohttp

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr

from .api import LinkivApi, LinkivAuthError, LinkivError
from .const import DOMAIN, EVENT, LONG_POLL_PERIOD, RETRY_MAX, RETRY_MIN, TRIGGERS, WS_FAILURES_BEFORE_LONG_POLL

if TYPE_CHECKING:
    from . import LinkivCoordinator

_LOGGER = logging.getLogger(__name__)

# Fermeture « accès retiré » envoyée par Linkivi (WebSocketCloseStatus.PolicyViolation)
CLOSE_ACCESS_REMOVED = 1008


class LinkivStream:
    """Tient le canal ouvert tant que l'intégration est chargée, et met à jour le coordinateur à chaque message."""

    def __init__(self, hass: HomeAssistant, coordinator: LinkivCoordinator, api: LinkivApi) -> None:
        self.hass = hass
        self.coordinator = coordinator
        self.api = api
        self.after: int | None = None
        self.connected = False
        self.mode: str | None = None
        self._ws: aiohttp.ClientWebSocketResponse | None = None

    async def send(self, message: dict[str, Any]) -> None:
        """Vers Linkivi (§303) : par le WebSocket ouvert, sinon en HTTPS (POST /stream/up). Une erreur d'envoi ne casse jamais le canal."""
        try:
            if self._ws is not None and not self._ws.closed:
                await self._ws.send_str(json.dumps(message, ensure_ascii=False))
            else:
                await self.api.stream_up(message)
        except (aiohttp.ClientError, LinkivError, ConnectionResetError, RuntimeError) as err:
            _LOGGER.debug("Linkivi : envoi impossible (%s)", err)

    async def _announce(self) -> None:
        share = getattr(self.coordinator, "share", None)
        if share is not None:
            await self.send(share.share_message())

    async def _answer(self, request: dict[str, Any]) -> None:
        share = getattr(self.coordinator, "share", None)
        if share is None:
            return
        reply = await share.answer(request)
        if reply is not None:
            await self.send(reply)

    async def run(self) -> None:
        """Boucle de vie du canal (tâche de fond de l'entrée : annulée au déchargement)."""
        delay = RETRY_MIN
        ws_failures = 0
        while True:
            try:
                if ws_failures < WS_FAILURES_BEFORE_LONG_POLL:
                    await self._websocket()
                else:
                    await self._long_poll(LONG_POLL_PERIOD)
                    ws_failures = 0
                delay = RETRY_MIN
            except asyncio.CancelledError:
                raise
            except LinkivAuthError as err:
                # accès retiré dans Linkivi, ou clé révoquée : demander une nouvelle autorisation
                _LOGGER.warning("Linkivi : accès refusé (%s), nouvelle autorisation nécessaire", err)
                self.connected = False
                self.coordinator.config_entry.async_start_reauth(self.hass)
                return
            except (aiohttp.ClientError, LinkivError, TimeoutError, ValueError) as err:
                if self.mode != "long_poll":
                    ws_failures += 1
                _LOGGER.debug("Linkivi : canal coupé (%s), nouvel essai dans %s s", err, delay)
            self.connected = False
            await asyncio.sleep(delay)
            delay = min(delay * 2, RETRY_MAX)

    async def _websocket(self) -> None:
        self.mode = "websocket"
        loop = asyncio.get_running_loop()
        opened = loop.time()
        try:
            async with self.api.session.ws_connect(self.api.stream_url(self.after), headers=self.api.auth_headers, heartbeat=30, max_msg_size=16 * 1024 * 1024) as ws:
                self.connected = True
                self._ws = ws
                await self._announce()   # ce qui est partagé avec Linkivi (§303)
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        self._handle(json.loads(msg.data))
                    elif msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        break
                self._ws = None
                if ws.close_code == CLOSE_ACCESS_REMOVED:
                    raise LinkivAuthError("Accès retiré dans Linkivi.")
        except aiohttp.WSServerHandshakeError as err:
            self._ws = None
            if err.status in (401, 403):
                raise LinkivAuthError(f"Accès refusé ({err.status}).") from err
            raise
        if loop.time() - opened < 30:
            # fermé presque aussitôt : un proxy qui laisse passer l'ouverture mais coupe la suite compte comme un échec
            raise LinkivError("Canal fermé aussitôt ouvert.")
        # fermeture normale (redémarrage du serveur…) : on se reconnecte

    async def _long_poll(self, period: float) -> None:
        self.mode = "long_poll"
        loop = asyncio.get_running_loop()
        end = loop.time() + period
        self._ws = None
        await self._announce()
        while loop.time() < end:
            body = await self.api.stream_next(self.after)
            self.connected = True
            for m in body.get("messages") or []:
                self._handle(m)
            nxt = body.get("next")
            if isinstance(nxt, int):
                self.after = nxt

    @callback
    def _handle(self, m: dict[str, Any]) -> None:
        kind = m.get("type")
        seq = m.get("seq")
        data = m.get("data") or {}
        if kind == "ping":
            return
        if kind == "ha.request":
            # une demande de Linkivi pour l'API de Home Assistant (§303) : réponse dans Home Assistant, entités partagées seulement
            if isinstance(seq, int) and (self.after is None or seq > self.after):
                self.after = seq
            self.hass.async_create_task(self._answer(data))
            return
        if isinstance(seq, int) and (self.after is None or seq > self.after or kind == "snapshot"):
            self.after = seq
        coordinator = self.coordinator

        if kind == "snapshot":
            coordinator.publish({s["id"]: s for s in data.get("screens") or [] if "id" in s})
            return
        if kind == "screen.changed" and "id" in data:
            coordinator.publish({**coordinator.all_screens, data["id"]: data})
            return
        if kind == "screen.removed" and "id" in data:
            coordinator.publish({k: v for k, v in coordinator.all_screens.items() if k != data["id"]})
            return

        # urgences en cours (capteur « Urgence en cours »)
        emergency = data.get("emergency") or {}
        if kind == "emergency.started" and emergency.get("id"):
            coordinator.emergencies = {**coordinator.emergencies, emergency["id"]: emergency.get("title", "")}
            coordinator.async_update_listeners()
        elif kind == "emergency.ended" and emergency.get("id"):
            coordinator.emergencies = {k: v for k, v in coordinator.emergencies.items() if k != emergency["id"]}
            coordinator.async_update_listeners()

        # événements de Linkivi (écran hors ligne, de retour, nouvelle version affichée, urgence…) : sur le bus de Home Assistant
        screen_id = (data.get("screen") or {}).get("id")
        device_id = None
        if screen_id:
            device = dr.async_get(self.hass).async_get_device(identifiers={(DOMAIN, screen_id)})
            device_id = device.id if device else None
        self.hass.bus.async_fire(
            EVENT,
            {"type": TRIGGERS.get(kind, kind), "event": kind, "screen_id": screen_id, "device_id": device_id, "data": data},
        )
