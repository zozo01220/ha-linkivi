"""Notification (§309) : une entité « notify » par écran, et une pour tous les écrans de l'organisation.

Elle sert dans toute automatisation ou blueprint qui « notifie » (action notify.send_message), et dans un groupe avec un téléphone.
Le message arrive en carte dans le coin bas droite, aspect « information », 15 s ; la diffusion continue. Pour choisir la place, le coin,
une image ou la durée : l'action linkivi.show_message.
"""

from __future__ import annotations

import logging

from homeassistant.components.notify import NotifyEntity, NotifyEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import LinkivError
from .const import DOMAIN
from .entity import LinkivEntity, add_new_screens
from .message import show

_LOGGER = logging.getLogger(__name__)

NOTIFY_DATA = {"place": "corner", "corner": "bottom_right", "look": "information"}


def _data(message: str, title: str | None) -> dict:
    # un message sans titre : il devient le titre de la carte (plus lisible de loin)
    if not title:
        return {**NOTIFY_DATA, "title": message[:60], "message": message[60:300].strip() or None}
    return {**NOTIFY_DATA, "title": title[:60], "message": message[:300]}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    entry.async_on_unload(add_new_screens(coordinator, async_add_entities, lambda sid, _s: [LinkivScreenNotify(coordinator, sid)]))
    async_add_entities([LinkivAllNotify(coordinator)])


class LinkivScreenNotify(LinkivEntity, NotifyEntity):
    """Notifier un écran : une carte en coin sur ce qu'il diffuse."""

    _attr_supported_features = NotifyEntityFeature.TITLE
    _attr_translation_key = "screen"

    def __init__(self, coordinator, screen_id: str) -> None:
        super().__init__(coordinator, screen_id, "notify")

    async def async_send_message(self, message: str, title: str | None = None) -> None:
        try:
            await show(self.hass, self.coordinator.api, self._screen_id, _data(message, title), None)
        except LinkivError as err:
            raise HomeAssistantError(f"{self.screen.get('name', 'Écran')} : {err}") from err


class LinkivAllNotify(CoordinatorEntity, NotifyEntity):
    """Notifier tous les écrans en ligne de l'organisation (les écrans hors ligne ou en veille sont passés)."""

    _attr_has_entity_name = True
    _attr_supported_features = NotifyEntityFeature.TITLE
    _attr_translation_key = "all_screens"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.org_id}_notify_all"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"org_{coordinator.org_id}")}, name=coordinator.org_name, manufacturer="Linkivi", model="Organisation",
            configuration_url=coordinator.api.base_url,
        )

    async def async_send_message(self, message: str, title: str | None = None) -> None:
        sent = 0
        for screen_id, screen in (self.coordinator.data or {}).items():
            if not screen.get("online") or screen.get("asleep"):
                continue
            try:
                await show(self.hass, self.coordinator.api, screen_id, _data(message, title), None)
                sent += 1
            except LinkivError as err:
                _LOGGER.debug("Linkivi : %s n'a pas reçu la notification (%s)", screen.get("name"), err)
        if sent == 0:
            raise HomeAssistantError("Aucun écran Linkivi en ligne et éveillé n'a reçu la notification.")
