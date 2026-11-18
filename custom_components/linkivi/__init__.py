"""Linkivi : voir et commander ses écrans depuis Home Assistant."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_URL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import LinkivApi, LinkivAuthError, LinkivError
from .const import CARD_FILE, CARD_URL, CARD_VERSION, DOMAIN, SCAN_INTERVAL
from .services import async_register_services
from .stream import LinkivStream

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SWITCH]


class LinkivCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Écrans de Linkivi indexés par identifiant : tenus à jour par le canal temps réel, relus en entier toutes les 5 min par sécurité."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: LinkivApi) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, config_entry=entry, update_interval=SCAN_INTERVAL)
        self.api = api
        # Plan Pro : commandes et messages permis (sur les autres plans, ni boutons ni interrupteur ni actions)
        self.pro: bool | None = None
        self.stream: LinkivStream | None = None

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            screens = await self.api.screens()
        except LinkivAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except LinkivError as err:
            raise UpdateFailed(str(err)) from err
        return {s["id"]: s for s in screens}


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Publie la carte « Écrans Linkivi » et la fait charger par l'interface ; déclare les actions."""
    path = Path(__file__).parent / "www" / CARD_FILE
    await hass.http.async_register_static_paths([StaticPathConfig(CARD_URL, str(path), False)])
    add_extra_js_url(hass, f"{CARD_URL}?v={CARD_VERSION}")
    await async_register_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Crée le client et le coordinateur, puis les entités, puis ouvre le canal temps réel."""
    api = LinkivApi(async_get_clientsession(hass), entry.data[CONF_URL], entry.data[CONF_API_KEY])
    coordinator = LinkivCoordinator(hass, entry, api)
    try:
        me = await api.me()
    except LinkivAuthError as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except LinkivError as err:
        raise ConfigEntryNotReady(str(err)) from err
    coordinator.pro = bool((me.get("organisation") or {}).get("pro", True))
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    coordinator.stream = LinkivStream(hass, coordinator, api)
    entry.async_create_background_task(hass, coordinator.stream.run(), f"{DOMAIN}_stream_{entry.entry_id}")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Intégration supprimée : sa clé est révoquée dans Linkivi (elle disparaît de Applications › Home Assistant)."""
    api = LinkivApi(async_get_clientsession(hass), entry.data[CONF_URL], entry.data[CONF_API_KEY])
    try:
        await api.revoke()
    except LinkivError as err:
        _LOGGER.info("Linkivi : la clé n'a pas pu être révoquée (%s) ; retirez l'accès dans Applications › Home Assistant", err)
