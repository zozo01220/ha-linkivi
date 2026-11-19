"""Aperçu du direct d'un écran (§301) : image de ce que l'écran affiche. Tous les plans (§307), players Android et Raspberry Pi."""

from __future__ import annotations

import time

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import LinkivError
from .entity import LinkivEntity, add_new_screens

# Une nouvelle capture est demandée à l'écran au plus toutes les 60 s (elle sollicite l'appareil) ; entre-temps, la dernière image est rendue.
REFRESH = 60


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data

    def build(screen_id: str, screen: dict) -> list:
        return [LinkivPreviewCamera(coordinator, screen_id)] if screen.get("capture") else []

    entry.async_on_unload(add_new_screens(coordinator, async_add_entities, build))


class LinkivPreviewCamera(LinkivEntity, Camera):
    _attr_translation_key = "preview"

    def __init__(self, coordinator, screen_id: str) -> None:
        LinkivEntity.__init__(self, coordinator, screen_id, "preview")
        Camera.__init__(self)
        self._asked = 0.0

    async def async_camera_image(self, width: int | None = None, height: int | None = None) -> bytes | None:
        api = self.coordinator.api
        if self.screen.get("online") and time.monotonic() - self._asked > REFRESH:
            self._asked = time.monotonic()
            try:
                await api.capture(self._screen_id)   # l'image arrive en quelques secondes : elle sera là au prochain rafraîchissement
            except LinkivError:
                pass
        try:
            return await api.capture_image(self._screen_id)
        except LinkivError:
            return None
