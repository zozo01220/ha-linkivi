"""Liste diffusée par un écran (§301) : la changer la publie aussitôt, sans approbation. Tous les plans."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import LinkivError
from .entity import LinkivEntity, add_new_screens


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    if "screens:playlist" not in coordinator.scopes:
        return   # ancienne clé sans cet accès : il vient avec une nouvelle autorisation par code
    entry.async_on_unload(
        add_new_screens(coordinator, async_add_entities, lambda sid, _s: [LinkivPlaylistSelect(coordinator, sid)])
    )


class LinkivPlaylistSelect(LinkivEntity, SelectEntity):
    _attr_translation_key = "playlist"

    def __init__(self, coordinator, screen_id: str) -> None:
        super().__init__(coordinator, screen_id, "playlist")

    @property
    def options(self) -> list[str]:
        names = sorted(set(self.coordinator.playlists.values()), key=str.casefold)
        current = self.current_option
        return names if current is None or current in names else [current, *names]

    @property
    def current_option(self) -> str | None:
        return (self.screen.get("playlist") or {}).get("name")

    async def async_select_option(self, option: str) -> None:
        pid = next((i for i, n in self.coordinator.playlists.items() if n == option), None)
        if pid is None:
            raise HomeAssistantError(f"Liste « {option} » introuvable dans Linkivi.")
        try:
            await self.coordinator.api.set_playlist(self._screen_id, pid)
        except LinkivError as err:
            raise HomeAssistantError(str(err)) from err
