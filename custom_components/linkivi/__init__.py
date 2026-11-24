"""Linkivi : voir et commander ses écrans depuis Home Assistant."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import SOURCE_INTEGRATION_DISCOVERY, ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_URL, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv, device_registry as dr, discovery_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.start import async_at_started
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import LinkivApi, LinkivAuthError, LinkivError
from .const import CARD_FILE, CARD_URL, CARD_VERSION, CONF_SCREENS, CONF_SEEN, DEVICE_LABELS, DISCOVERY_PREFIX, DOMAIN, OPT_AUTO_ADD, SCAN_INTERVAL, hardware
from .services import async_register_services
from .share import OPT_AREAS, OPT_COMMANDS, OPT_ENTITIES, OPT_LABELS, LinkivShare
from .stream import LinkivStream
from .update_check import async_watch_updates

_LOGGER = logging.getLogger(__name__)

# Rien à configurer en YAML : tout passe par l'interface (contrôle hassfest)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.CAMERA, Platform.NOTIFY, Platform.SELECT, Platform.SENSOR, Platform.SWITCH]


class LinkivCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Écrans de Linkivi indexés par identifiant : tenus à jour par le canal temps réel, relus en entier toutes les 5 min par sécurité."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: LinkivApi) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, config_entry=entry, update_interval=SCAN_INTERVAL)
        self.api = api
        self.stream: LinkivStream | None = None
        # Accès de la clé (/me) : une autorisation d'avant la 1.7.1 peut manquer l'urgence
        self.scopes: set[str] = set()
        self.org_id: str = ""
        self.org_name: str = "Linkivi"
        # Listes de lecture (id → nom), relues avec les écrans ; urgences en cours (id → titre), tenues par le canal
        self.playlists: dict[str, str] = {}
        self.emergencies: dict[str, str] = {}
        # Partage avec Linkivi (§303) : entités montrées sur les écrans sans jeton chez Linkivi
        self.key_id: str = ""
        self.share: LinkivShare | None = None
        # Écrans (§337) : tous ceux du compte ; « data » ne garde que ceux que Home Assistant suit (appareils)
        self.all_screens: dict[str, dict[str, Any]] = {}
        screens = entry.data.get(CONF_SCREENS)
        self.tracked: set[str] | None = None if screens is None else set(screens)
        self.seen: set[str] = set(entry.data.get(CONF_SEEN) or screens or [])
        self._announced: set[str] = set()   # écrans proposés dans Découvertes depuis le démarrage
        self.share_options = _share_options(entry)

    @property
    def auto_add(self) -> bool:
        return bool(self.config_entry.options.get(OPT_AUTO_ADD, False))

    @callback
    def set_screens(self, screens: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Garde tous les écrans du compte, rend ceux que Home Assistant suit et propose les autres dans Découvertes.

        Première fois (installation, ou passage à la 1.12) : tous les écrans déjà là sont suivis.
        Ensuite, un écran jamais vu est suivi tout de suite si « Ajouter automatiquement » est coché ;
        sinon, comme un écran retiré de Home Assistant, il attend dans Découvertes.
        """
        self.all_screens = screens
        if self.tracked is None:
            self._save(set(screens), set(screens))
        else:
            new = set(screens) - self.seen
            if new:
                self._save(self.tracked | new if self.auto_add else self.tracked, self.seen | new)
        self._announce()
        tracked = {k: v for k, v in screens.items() if k in (self.tracked or set())}
        self._sync_devices(tracked)
        return tracked

    @callback
    def _sync_devices(self, screens: dict[str, dict[str, Any]]) -> None:
        """Fiche de l'appareil (§349) : version du player, modèle et système suivent ce que Linkivi a reçu du player (mise à jour, changement de boîtier)."""
        device_reg = dr.async_get(self.hass)
        for sid, screen in screens.items():
            device = device_reg.async_get_device(identifiers={(DOMAIN, sid)})
            if device is None:
                continue   # appareil pas encore créé : ses entités le créeront avec ces valeurs
            hw, sw = hardware(screen), screen.get("playerVersion")
            if (hw and hw != device.hw_version) or (sw and sw != device.sw_version):
                device_reg.async_update_device(device.id, hw_version=hw or device.hw_version, sw_version=sw or device.sw_version)

    @callback
    def publish(self, screens: dict[str, dict[str, Any]]) -> None:
        """Écrans reçus par le canal temps réel (ou options changées) : même tri que la relecture complète."""
        self.async_set_updated_data(self.set_screens(screens))

    @callback
    def _save(self, tracked: set[str], seen: set[str]) -> None:
        self.tracked, self.seen = tracked, seen
        entry = self.config_entry
        self.hass.config_entries.async_update_entry(entry, data={**entry.data, CONF_SCREENS: sorted(tracked), CONF_SEEN: sorted(seen)})

    @callback
    def _announce(self) -> None:
        """Un écran non suivi → une découverte (une seule par démarrage ; « Ignorer » est géré par Home Assistant) ; écran supprimé → découverte retirée."""
        waiting = set(self.all_screens) - (self.tracked or set())
        for sid in waiting - self._announced:
            screen = self.all_screens[sid]
            discovery_flow.async_create_flow(
                self.hass, DOMAIN, context={"source": SOURCE_INTEGRATION_DISCOVERY},
                data={"entry_id": self.config_entry.entry_id, "screen_id": sid, "name": screen.get("name") or "Écran", "model": DEVICE_LABELS.get(screen.get("device"), "Écran")},
            )
        for sid in self._announced - waiting:
            self.forget_discovery(sid)
        self._announced = waiting

    @callback
    def forget_discovery(self, sid: str) -> None:
        """Retire la découverte en attente d'un écran (supprimé dans Linkivi, ou ajouté par un autre chemin)."""
        flows = self.hass.config_entries.flow
        for flow in flows.async_progress_by_handler(DOMAIN, match_context={"unique_id": f"{DISCOVERY_PREFIX}{sid}"}):
            flows.async_abort(flow["flow_id"])
        self._announced.discard(sid)

    @callback
    def add_screen(self, sid: str, area_id: str | None = None) -> bool:
        """« Ajouter » dans Découvertes : l'écran devient un appareil, rangé tout de suite dans la pièce choisie."""
        screen = self.all_screens.get(sid)
        if screen is None:
            return False
        device_reg = dr.async_get(self.hass)
        device = device_reg.async_get_or_create(
            config_entry_id=self.config_entry.entry_id,
            identifiers={(DOMAIN, sid)},
            name=screen.get("name") or "Écran",
            manufacturer="Linkivi",
            model=DEVICE_LABELS.get(screen.get("device"), "Écran"),
            hw_version=hardware(screen),
            sw_version=screen.get("playerVersion"),
            configuration_url=self.api.base_url,
        )
        if area_id:
            device_reg.async_update_device(device.id, area_id=area_id)
        self._announced.discard(sid)
        self._save((self.tracked or set()) | {sid}, self.seen | {sid})
        self.publish(self.all_screens)
        return True

    @callback
    def remove_screen(self, sid: str) -> None:
        """Appareil supprimé dans Home Assistant : l'écran n'est plus suivi et retourne dans Découvertes."""
        if self.tracked and sid in self.tracked:
            self._save(self.tracked - {sid}, self.seen | {sid})
            self.publish(self.all_screens)

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            screens = await self.api.screens()
            self.playlists = {p["id"]: p.get("name", "") for p in await self.api.playlists()}
            if "emergency:read" in self.scopes:
                self.emergencies = {e["id"]: e.get("title", "") for e in await self.api.emergencies()}
        except LinkivAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except LinkivError as err:
            raise UpdateFailed(str(err)) from err
        return self.set_screens({s["id"]: s for s in screens})


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Publie la carte « Écrans Linkivi » et la fait charger par l'interface ; déclare les actions."""
    path = Path(__file__).parent / "www" / CARD_FILE
    await hass.http.async_register_static_paths([StaticPathConfig(CARD_URL, str(path), False)])
    add_extra_js_url(hass, f"{CARD_URL}?v={CARD_VERSION}")
    await async_register_services(hass)
    await async_watch_updates(hass)   # après une mise à jour par HACS : réparation « Redémarrage nécessaire » (§310)
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
    org = me.get("organisation") or {}
    coordinator.org_id = str(org.get("id") or entry.entry_id)
    coordinator.org_name = org.get("name") or "Linkivi"
    coordinator.scopes = set((me.get("key") or {}).get("scopes") or [])
    coordinator.key_id = str((me.get("key") or {}).get("id") or "")
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    coordinator.stream = LinkivStream(hass, coordinator, api)
    coordinator.share = LinkivShare(hass, coordinator)
    coordinator.share.compute()
    coordinator.share.watch(coordinator.stream.send)
    entry.async_on_unload(coordinator.share.stop)

    async def _started(_hass: HomeAssistant) -> None:
        # Home Assistant a fini de démarrer : partage renvoyé avec toutes les entités qui ont maintenant un état (1.10.1)
        if coordinator.stream and coordinator.share:
            await coordinator.stream.send(coordinator.share.share_message())

    entry.async_on_unload(async_at_started(hass, _started))
    entry.async_on_unload(entry.add_update_listener(_options_changed))
    entry.async_create_background_task(hass, coordinator.stream.run(), f"{DOMAIN}_stream_{entry.entry_id}")
    return True


def _share_options(entry: ConfigEntry) -> dict[str, Any]:
    return {k: entry.options.get(k) for k in (OPT_AREAS, OPT_LABELS, OPT_ENTITIES, OPT_COMMANDS)}


async def _options_changed(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Entrée modifiée : « Ajouter automatiquement » pris en compte ; partage modifié → Linkivi prévenu tout de suite."""
    coordinator = entry.runtime_data
    coordinator.publish(coordinator.all_screens)
    share = _share_options(entry)
    if share == coordinator.share_options:
        return   # seule la liste des écrans suivis a changé
    coordinator.share_options = share
    if coordinator.stream and coordinator.share:
        await coordinator.stream.send(coordinator.share.share_message())


async def async_remove_config_entry_device(hass: HomeAssistant, entry: ConfigEntry, device: dr.DeviceEntry) -> bool:
    """« Supprimer l'appareil » permis pour un écran (il retourne dans Découvertes), jamais pour l'organisation."""
    coordinator = getattr(entry, "runtime_data", None)
    ids = [ident for domain, ident in device.identifiers if domain == DOMAIN]
    if coordinator is None or not ids or ids[0].startswith("org_"):
        return False
    coordinator.remove_screen(ids[0])
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
