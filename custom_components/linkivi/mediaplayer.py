"""Musique en cours d'un lecteur de Home Assistant (§351) : titre, artiste, album, position et pochette, pour l'action show_mediaplayer_playing.

Alexa Media Player, Sonos, Spotify… donnent tous ces attributs standard. La pochette est lue ici, dans Home Assistant (même chemin que l'interface),
puis envoyée à Linkivi : l'écran ne contacte jamais le lecteur.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

from .const import MAX_IMAGE_BYTES
from .message import url_image

_LOGGER = logging.getLogger(__name__)

MAX_TITLE = 60   # limite de Linkivi pour un titre


def _image_ok(data: bytes | None) -> bool:
    """JPEG, PNG ou WebP de 3 Mo au plus : ce que Linkivi accepte (sinon l'affichage serait refusé, on l'envoie sans pochette)."""
    if not data or len(data) > MAX_IMAGE_BYTES or len(data) < 13:
        return False
    return data[:2] == b"\xff\xd8" or data[:4] == b"\x89PNG" or (data[:4] == b"RIFF" and data[8:12] == b"WEBP")


async def _cover(hass: HomeAssistant, entity_id: str, picture: str | None) -> bytes | None:
    """Pochette du morceau : demandée à l'entité du lecteur (comme l'interface), sinon lue à son adresse si elle est complète. Jamais bloquante."""
    try:
        component = hass.data.get("media_player")   # EntityComponent des lecteurs
        entity = component.get_entity(entity_id) if component is not None else None
        if entity is not None:
            data, _type = await entity.async_get_media_image()
            if _image_ok(data):
                return data
    except Exception as err:   # pochette absente ou illisible : le morceau s'affiche quand même
        _LOGGER.debug("Linkivi : pochette de %s illisible (%s)", entity_id, err)
    if picture and picture.startswith(("http://", "https://")):
        try:
            data = await url_image(hass, picture)
            if _image_ok(data):
                return data
        except Exception as err:
            _LOGGER.debug("Linkivi : pochette de %s illisible à son adresse (%s)", entity_id, err)
    return None


def _iso(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value) if value else None


async def now_playing(hass: HomeAssistant, entity_id: str) -> tuple[str, dict[str, Any], bytes | None]:
    """(titre, musique pour Linkivi, pochette) du morceau en cours ; erreur claire si rien ne joue."""
    st = hass.states.get(entity_id)
    if st is None:
        raise ServiceValidationError(f"Lecteur {entity_id} introuvable.")
    if st.state != "playing":
        raise ServiceValidationError(f"Rien n'est en cours de lecture sur {st.attributes.get('friendly_name') or entity_id}.")
    a = st.attributes
    title = str(a.get("media_title") or "").strip()
    if not title:
        raise ServiceValidationError("Le lecteur ne donne pas le titre du morceau.")
    if len(title) > MAX_TITLE:
        title = title[: MAX_TITLE - 1].rstrip() + "…"
    music = {
        "artist": str(a.get("media_artist") or a.get("media_album_artist") or ""),
        "album": str(a.get("media_album_name") or ""),
        "source": str(a.get("friendly_name") or entity_id),
        "positionSeconds": a.get("media_position"),
        "durationSeconds": a.get("media_duration"),
        "positionAt": _iso(a.get("media_position_updated_at")),
    }
    return title, music, await _cover(hass, entity_id, a.get("entity_picture"))
