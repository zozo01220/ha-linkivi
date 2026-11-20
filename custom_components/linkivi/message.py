"""Envoi d'un message à un écran (§309) : image d'une caméra ou d'une adresse lue ici, dans Home Assistant, puis envoyée à Linkivi.

L'écran ne contacte jamais la caméra ni l'adresse : il reçoit l'image de Linkivi. Avec « live », l'image d'une caméra est relue et renvoyée
toutes les 2 s tant que le message est affiché. Utilisé par l'action show_message, l'entité de notification et les actions d'appareil.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import LinkivError
from .const import LIVE_IMAGE_SECONDS, MAX_IMAGE_BYTES

_LOGGER = logging.getLogger(__name__)

DEFAULT_SECONDS = {"corner": 15}   # sinon 30 s (règle de Linkivi, rappelée ici pour la durée de l'image « En direct »)


async def camera_image(hass: HomeAssistant, entity_id: str) -> bytes:
    """Image du moment d'une caméra de Home Assistant (JPEG le plus souvent)."""
    from homeassistant.components.camera import async_get_image   # import tardif : la caméra n'est pas une dépendance obligatoire

    try:
        image = await async_get_image(hass, entity_id, timeout=10)
    except HomeAssistantError as err:
        raise HomeAssistantError(f"Image de {entity_id} indisponible : {err}") from err
    if len(image.content) > MAX_IMAGE_BYTES:
        raise HomeAssistantError(f"L'image de {entity_id} dépasse 3 Mo.")
    return image.content


async def url_image(hass: HomeAssistant, url: str) -> bytes:
    """Image lue à une adresse (3 Mo au plus)."""
    try:
        async with async_get_clientsession(hass).get(url, timeout=aiohttp.ClientTimeout(total=15)) as res:
            if res.status != 200:
                raise HomeAssistantError(f"L'adresse de l'image répond {res.status}.")
            body = await res.content.read(MAX_IMAGE_BYTES + 1)
    except (aiohttp.ClientError, asyncio.TimeoutError) as err:
        raise HomeAssistantError(f"Image illisible à cette adresse : {err}") from err
    if len(body) > MAX_IMAGE_BYTES:
        raise HomeAssistantError("L'image dépasse 3 Mo.")
    return body


async def read_image(hass: HomeAssistant, camera: str | None, image_url: str | None) -> bytes | None:
    if camera:
        return await camera_image(hass, camera)
    if image_url:
        return await url_image(hass, image_url)
    return None


async def show(
    hass: HomeAssistant,
    api: Any,
    screen_id: str,
    data: dict[str, Any],
    image: bytes | None,
) -> None:
    """Affiche le message sur un écran ; démarre le rafraîchissement de l'image si « live » est demandé pour une caméra."""
    place = data.get("place") or "full"
    res = await api.display(
        screen_id,
        title=data.get("title"),
        message=data.get("message"),
        look=data.get("look") or "information",
        blur=bool(data.get("blur")) and place == "full",
        duration=data.get("duration"),
        wake=bool(data.get("wake")),
        place=place,
        corner=data.get("corner") if place == "corner" else None,
        tag=data.get("tag"),
        image=image,
        live=bool(data.get("live")) and bool(data.get("camera")),
    )
    notice_id = res.get("noticeId")
    if image and notice_id and data.get("live") and data.get("camera"):
        seconds = data.get("duration") or DEFAULT_SECONDS.get(place, 30)
        hass.async_create_background_task(_live(hass, api, screen_id, str(notice_id), data["camera"], seconds), f"linkivi_live_{notice_id}")


async def _live(hass: HomeAssistant, api: Any, screen_id: str, notice_id: str, camera: str, seconds: int) -> None:
    """Image « En direct » : relue et renvoyée toutes les 2 s jusqu'à la fin du message (ou dès que Linkivi dit qu'il n'est plus affiché)."""
    loop = asyncio.get_running_loop()
    end = loop.time() + seconds
    while loop.time() + LIVE_IMAGE_SECONDS < end:
        await asyncio.sleep(LIVE_IMAGE_SECONDS)
        try:
            await api.display_image(screen_id, notice_id, await camera_image(hass, camera))
        except LinkivError:
            return   # message retiré ou remplacé
        except HomeAssistantError as err:
            _LOGGER.debug("Linkivi : image en direct de %s non relue (%s)", camera, err)
