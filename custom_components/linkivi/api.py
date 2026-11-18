"""Client de l'API publique de Linkivi (accès par clé, https://…/docs/api)."""

from __future__ import annotations

from typing import Any

import aiohttp

from .const import API_PATH


class LinkivError(Exception):
    """Linkivi n'a pas pu répondre, ou a refusé la demande (le texte dit pourquoi)."""


class LinkivAuthError(LinkivError):
    """Clé inconnue, révoquée, expirée ou sans l'accès nécessaire."""


def clean_url(url: str) -> str:
    """« linkivi.exemple.ch/ » → « https://linkivi.exemple.ch »."""
    url = (url or "").strip().rstrip("/")
    if url and "://" not in url:
        url = "https://" + url
    return url


async def _json(res: aiohttp.ClientResponse) -> dict[str, Any]:
    try:
        body = await res.json(content_type=None)
    except (aiohttp.ContentTypeError, ValueError):
        body = {}
    return body if isinstance(body, dict) else {}


async def pair_start(session: aiohttp.ClientSession, base_url: str, name: str) -> dict[str, Any]:
    """Demande un code d'appairage (sans clé) : userCode, deviceCode, verificationUrlComplete, expiresIn, interval."""
    url = f"{clean_url(base_url)}{API_PATH}/ha/pair"
    try:
        async with session.post(url, json={"name": name}, timeout=aiohttp.ClientTimeout(total=15)) as res:
            body = await _json(res)
            if res.status != 200 or "deviceCode" not in body:
                raise LinkivError(body.get("detail") or f"Erreur {res.status}.")
            return body
    except aiohttp.ClientError as err:
        raise LinkivError(f"Linkivi est injoignable : {err}") from err
    except TimeoutError as err:
        raise LinkivError("Linkivi ne répond pas.") from err


async def pair_token(session: aiohttp.ClientSession, base_url: str, device_code: str) -> tuple[str, dict[str, Any]]:
    """Relève la réponse : « pending », « approved » (avec apiKey et organisation), « denied », « expired » ou « unknown »."""
    url = f"{clean_url(base_url)}{API_PATH}/ha/pair/token"
    try:
        async with session.post(url, json={"deviceCode": device_code}, timeout=aiohttp.ClientTimeout(total=15)) as res:
            body = await _json(res)
            status = {200: "approved", 202: "pending", 403: "denied", 410: "expired", 404: "unknown"}.get(res.status)
            if status is None:
                raise LinkivError(body.get("detail") or f"Erreur {res.status}.")
            return status, body
    except aiohttp.ClientError as err:
        raise LinkivError(f"Linkivi est injoignable : {err}") from err
    except TimeoutError as err:
        raise LinkivError("Linkivi ne répond pas.") from err


class LinkivApi:
    """Les appels dont l'intégration a besoin : /me, /screens, commandes, messages et canal temps réel."""

    def __init__(self, session: aiohttp.ClientSession, base_url: str, api_key: str) -> None:
        self.session = session
        self.base_url = clean_url(base_url)
        self.auth_headers = {"Authorization": f"Bearer {api_key}"}
        self._headers = {**self.auth_headers, "Accept": "application/json"}

    async def _request(self, method: str, path: str, *, timeout: float = 15, **kwargs: Any) -> dict[str, Any]:
        url = f"{self.base_url}{API_PATH}{path}"
        try:
            async with self.session.request(
                method, url, headers=self._headers, timeout=aiohttp.ClientTimeout(total=timeout), **kwargs
            ) as res:
                body = await _json(res)
                if res.status < 300:
                    return body
                # application/problem+json : « code » stable, « detail » lisible
                detail = body.get("detail") or body.get("title") or ""
                if res.status == 401 or res.status == 403 and body.get("code") in ("scope_missing", "key_revoked", "invalid_key"):
                    raise LinkivAuthError(detail or f"Accès refusé ({res.status}).")
                raise LinkivError(detail or f"Erreur {res.status}.")
        except aiohttp.ClientError as err:
            raise LinkivError(f"Linkivi est injoignable : {err}") from err
        except TimeoutError as err:
            raise LinkivError("Linkivi ne répond pas.") from err

    async def me(self) -> dict[str, Any]:
        """Organisation (« pro » : commandes et messages permis) et clé (accès account:read)."""
        return await self._request("GET", "/me")

    async def revoke(self) -> None:
        """Révoque la clé de l'intégration (appelé quand on supprime l'intégration)."""
        await self._request("DELETE", "/me")

    async def screens(self) -> list[dict[str, Any]]:
        """Tous les écrans appairés, en suivant le curseur de pagination."""
        result: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            params: dict[str, Any] = {"limit": 200}
            if cursor:
                params["cursor"] = cursor
            page = await self._request("GET", "/screens", params=params)
            result.extend(page.get("data", []))
            cursor = page.get("next")
            if not cursor:
                return result

    def stream_url(self, after: int | None) -> str:
        """Adresse du canal temps réel (WebSocket) ; « after » : reprendre sans perte après une coupure."""
        url = self.base_url.replace("https://", "wss://", 1).replace("http://", "ws://", 1) + f"{API_PATH}/stream"
        return url if after is None else f"{url}?after={after}"

    async def stream_up(self, message: dict[str, Any]) -> None:
        """Message de l'intégration vers Linkivi quand le WebSocket ne passe pas (réponses, signaux : §303)."""
        await self._request("POST", "/stream/up", json=message, timeout=30)

    async def stream_next(self, after: int | None) -> dict[str, Any]:
        """Le même canal en attente longue (HTTPS simple) : rend après 25 s au plus."""
        params = {} if after is None else {"after": after}
        return await self._request("GET", "/stream/next", timeout=45, params=params)

    async def command(self, screen_id: str, command: str) -> dict[str, Any]:
        """Envoie une commande à un écran ; lève LinkivError avec la raison si Linkivi la refuse."""
        return await self._request("POST", f"/screens/{screen_id}/commands", json={"command": command})

    async def display(
        self,
        screen_id: str,
        *,
        title: str | None,
        message: str | None,
        look: str,
        duration: int,
        wake: bool,
        place: str = "full",
    ) -> dict[str, Any]:
        """Affiche un message un moment par-dessus la diffusion (accès screens:control) ; Linkivi dit pourquoi il refuse (écran hors ligne, en veille…)."""
        body: dict[str, Any] = {"look": look, "durationSeconds": duration, "wake": wake, "place": place}
        if title:
            body["title"] = title
        if message:
            body["message"] = message
        return await self._request("POST", f"/screens/{screen_id}/display", json=body)

    async def clear_display(self, screen_id: str) -> dict[str, Any]:
        """Retire le message affiché : la diffusion reprend."""
        return await self._request("DELETE", f"/screens/{screen_id}/display")

    # ---------- lot 2 (§301) : listes, aperçu du direct, urgence ----------

    async def playlists(self) -> list[dict[str, Any]]:
        """Listes de lecture de l'organisation (id, name)."""
        return (await self._request("GET", "/playlists")).get("data", [])

    async def set_playlist(self, screen_id: str, playlist_id: str) -> dict[str, Any]:
        """Change la liste diffusée par un écran ; publiée aussitôt, sans approbation."""
        return await self._request("PUT", f"/screens/{screen_id}/playlist", json={"playlistId": playlist_id})

    async def capture(self, screen_id: str) -> dict[str, Any]:
        """Demande un aperçu du direct (Pro, Android et Raspberry Pi)."""
        return await self._request("POST", f"/screens/{screen_id}/capture")

    async def capture_image(self, screen_id: str) -> bytes | None:
        """Dernier aperçu du direct (JPEG), ou None s'il n'y en a pas encore."""
        url = f"{self.base_url}{API_PATH}/screens/{screen_id}/capture"
        try:
            async with self.session.get(url, headers=self.auth_headers, timeout=aiohttp.ClientTimeout(total=15)) as res:
                if res.status == 200:
                    return await res.read()
                if res.status == 401:
                    raise LinkivAuthError("Accès refusé (401).")
                return None
        except aiohttp.ClientError as err:
            raise LinkivError(f"Linkivi est injoignable : {err}") from err
        except TimeoutError as err:
            raise LinkivError("Linkivi ne répond pas.") from err

    async def emergencies(self) -> list[dict[str, Any]]:
        """Urgences en cours (accès emergency:read)."""
        return (await self._request("GET", "/emergency")).get("data", [])

    async def start_emergency(self, title: str, message: str | None, screens: list[str] | None, source: str) -> dict[str, Any]:
        """Déclenche une urgence : sur ces écrans, ou sur tous (screens vide)."""
        targets: dict[str, Any] = {"screens": screens} if screens else {"all": True}
        body: dict[str, Any] = {"title": title, "targets": targets, "source": source}
        if message:
            body["message"] = message
        return await self._request("POST", "/emergency", json=body)

    async def end_emergency(self, emergency_id: str) -> dict[str, Any]:
        """Lève une urgence."""
        return await self._request("DELETE", f"/emergency/{emergency_id}")
