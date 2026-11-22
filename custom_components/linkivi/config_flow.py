"""Ajout de Linkivi (§299, lot 1) : avec un code à vérifier dans Linkivi (proposé), ou en collant une clé d'API (avancé).

Nouveaux écrans (§337) : proposés un par un dans Découvertes ; « Ajouter » en fait un appareil, rangé dans la pièce choisie.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import SOURCE_REAUTH, SOURCE_RECONFIGURE, ConfigEntry, ConfigEntryState, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import DiscoveryInfoType

from .api import LinkivApi, LinkivAuthError, LinkivError, clean_url, pair_start, pair_token
from .const import DEFAULT_URL, DISCOVERY_PREFIX, DOMAIN, OPT_AUTO_ADD
from .share import OPT_AREAS, OPT_COMMANDS, OPT_ENTITIES, OPT_LABELS


class LinkivConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return LinkivOptionsFlow()

    def __init__(self) -> None:
        self._url = DEFAULT_URL
        self._pair: dict[str, Any] | None = None
        self._task: asyncio.Task[dict[str, Any] | None] | None = None
        self._result: dict[str, Any] | None = None
        self._failure = "expired"
        self._screen: dict[str, Any] = {}

    # ---------- départ : le menu ----------

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_show_menu(step_id="user", menu_options=["code", "key"])

    # ---------- avec un code (appairage) ----------

    async def async_step_code(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """L'adresse de Linkivi, puis la demande d'un code."""
        errors: dict[str, str] = {}
        if user_input is not None:
            url = clean_url(user_input[CONF_URL])
            try:
                self._pair = await pair_start(async_get_clientsession(self.hass), url, self.hass.config.location_name or "Home Assistant")
            except LinkivError:
                errors["base"] = "cannot_connect"
            else:
                self._url = url
                return await self.async_step_wait()
        schema = vol.Schema({vol.Required(CONF_URL, default=self._url): str})
        return self.async_show_form(step_id="code", data_schema=schema, errors=errors)

    async def async_step_wait(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Affiche le lien et le code, et attend « Autoriser » dans Linkivi (relevé toutes les 5 s, 10 min au plus)."""
        assert self._pair is not None
        if self._task is None:
            self._task = self.hass.async_create_task(self._poll())
        if not self._task.done():
            return self.async_show_progress(
                step_id="wait",
                progress_action="wait",
                progress_task=self._task,
                description_placeholders={"url": self._pair["verificationUrlComplete"], "code": self._pair["userCode"]},
            )
        try:
            self._result = self._task.result()
        except Exception:  # noqa: BLE001 — une erreur inattendue de la tâche vaut un échec, jamais un plantage du parcours
            self._result = None
            self._failure = "cannot_connect"
        self._task = None
        return self.async_show_progress_done(next_step_id="finish" if self._result else "failed")

    async def _poll(self) -> dict[str, Any] | None:
        assert self._pair is not None
        session = async_get_clientsession(self.hass)
        interval = max(2, int(self._pair.get("interval", 5)))
        loop = asyncio.get_running_loop()
        deadline = loop.time() + int(self._pair.get("expiresIn", 600))
        while loop.time() < deadline:
            await asyncio.sleep(interval)
            try:
                status, body = await pair_token(session, self._url, self._pair["deviceCode"])
            except LinkivError:
                continue   # coupure passagère : on redemande au tour suivant
            if status == "approved":
                return body
            if status in ("denied", "expired", "unknown"):
                self._failure = "denied" if status == "denied" else "expired"
                return None
        self._failure = "expired"
        return None

    async def async_step_failed(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_abort(reason=self._failure)

    async def async_step_finish(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        assert self._result is not None
        key = self._result["apiKey"]
        org = self._result.get("organisation") or {}
        if self.source == SOURCE_REAUTH:
            return self.async_update_reload_and_abort(self._get_reauth_entry(), data_updates={CONF_URL: self._url, CONF_API_KEY: key})
        if self.source == SOURCE_RECONFIGURE:
            entry = self._get_reconfigure_entry()
            if org.get("id") and entry.unique_id != str(org["id"]):
                return self.async_abort(reason="wrong_account")   # autorisé dans une autre organisation : on garde l'ancien accès
            return self.async_update_reload_and_abort(entry, data_updates={CONF_URL: self._url, CONF_API_KEY: key})
        await self.async_set_unique_id(str(org.get("id") or self._url))
        self._abort_if_unique_id_configured(updates={CONF_URL: self._url, CONF_API_KEY: key})
        return self.async_create_entry(title=org.get("name") or "Linkivi", data={CONF_URL: self._url, CONF_API_KEY: key})

    # ---------- avancé : coller une clé d'API ----------

    async def _check(self, url: str, key: str) -> tuple[dict[str, Any] | None, str | None]:
        """Essaie la clé : l'organisation si elle marche, sinon le code d'erreur à afficher."""
        api = LinkivApi(async_get_clientsession(self.hass), url, key)
        try:
            me = await api.me()
            await api.screens()  # vérifie aussi l'accès « Écrans »
        except LinkivAuthError:
            return None, "invalid_auth"
        except LinkivError:
            return None, "cannot_connect"
        return me, None

    async def async_step_key(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            url = clean_url(user_input[CONF_URL])
            key = user_input[CONF_API_KEY].strip()
            me, error = await self._check(url, key)
            if me is not None:
                org = me.get("organisation", {})
                await self.async_set_unique_id(str(org.get("id", url)))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=org.get("name") or "Linkivi", data={CONF_URL: url, CONF_API_KEY: key})
            errors["base"] = error or "unknown"
        schema = vol.Schema(
            {
                vol.Required(CONF_URL, default=(user_input or {}).get(CONF_URL, self._url)): str,
                vol.Required(CONF_API_KEY): str,
            }
        )
        return self.async_show_form(step_id="key", data_schema=schema, errors=errors)

    # ---------- « Reconfigurer » (menu ⋮ de l'intégration) : refaire l'autorisation par code ----------

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Nouvelle autorisation sans supprimer l'intégration (ex. une autorisation d'avant la 1.7.1, sans l'urgence) : entités et partage gardés."""
        self._url = self._get_reconfigure_entry().data.get(CONF_URL, DEFAULT_URL)
        return await self.async_step_code()

    # ---------- nouvelle autorisation (accès retiré, clé révoquée ou expirée) ----------

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        self._url = entry_data.get(CONF_URL, DEFAULT_URL)
        return self.async_show_menu(step_id="reauth_confirm", menu_options=["code", "reauth_key"])

    async def async_step_reauth_key(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Coller une nouvelle clé (modèle « Home Assistant »)."""
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            key = user_input[CONF_API_KEY].strip()
            me, error = await self._check(entry.data[CONF_URL], key)
            if me is not None:
                return self.async_update_reload_and_abort(entry, data_updates={CONF_API_KEY: key})
            errors["base"] = error or "unknown"
        return self.async_show_form(step_id="reauth_key", data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}), errors=errors)

    # ---------- un nouvel écran, proposé dans Découvertes (§337) ----------

    async def async_step_integration_discovery(self, discovery_info: DiscoveryInfoType) -> ConfigFlowResult:
        """Annoncé par l'intégration déjà configurée : un écran de Linkivi que Home Assistant ne suit pas encore."""
        await self.async_set_unique_id(f"{DISCOVERY_PREFIX}{discovery_info['screen_id']}")
        self._abort_if_unique_id_configured()   # écran ignoré
        self._screen = dict(discovery_info)
        return await self.async_step_discovery_confirm()

    async def async_step_unignore(self, user_input: dict[str, Any]) -> ConfigFlowResult:
        """« Ne plus ignorer » : l'écran est proposé de nouveau, s'il existe toujours dans Linkivi."""
        unique_id = user_input["unique_id"]
        sid = unique_id.removeprefix(DISCOVERY_PREFIX)
        await self.async_set_unique_id(unique_id)
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            coordinator = getattr(entry, "runtime_data", None)
            if coordinator is not None and entry.state is ConfigEntryState.LOADED and sid in coordinator.all_screens:
                screen = coordinator.all_screens[sid]
                self._screen = {"entry_id": entry.entry_id, "screen_id": sid, "name": screen.get("name") or "Écran", "model": ""}
                return await self.async_step_discovery_confirm()
        return self.async_abort(reason="screen_gone")

    def _hub(self) -> Any:
        entry = self.hass.config_entries.async_get_entry(self._screen.get("entry_id", ""))
        if entry is None or entry.state is not ConfigEntryState.LOADED:
            return None
        return entry

    async def async_step_discovery_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Le nom de l'écran et la pièce où le ranger ; « Valider » l'ajoute à l'organisation Linkivi déjà connectée."""
        name = self._screen.get("name") or "Écran"
        self.context["title_placeholders"] = {"name": name}
        hub = self._hub()
        if hub is None:
            return self.async_abort(reason="not_loaded")
        if user_input is not None:
            if not hub.runtime_data.add_screen(self._screen["screen_id"], user_input.get("area_id")):
                return self.async_abort(reason="screen_gone")
            return self.async_abort(reason="screen_added", description_placeholders={"name": name})
        schema = vol.Schema({vol.Optional("area_id"): selector.AreaSelector()})
        return self.async_show_form(
            step_id="discovery_confirm",
            data_schema=schema,
            description_placeholders={"name": name, "model": self._screen.get("model") or "Écran", "org": hub.title},
        )


class LinkivOptionsFlow(OptionsFlow):
    """« Partager avec Linkivi » (§303) : ce que les écrans de Linkivi voient de cette maison, et s'ils peuvent commander ces appareils.

    En tête (§337) : « Ajouter automatiquement les nouveaux écrans » (sinon ils attendent dans Découvertes).
    """

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        o = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(OPT_AUTO_ADD, default=o.get(OPT_AUTO_ADD, False)): selector.BooleanSelector(),
                vol.Optional(OPT_AREAS, default=o.get(OPT_AREAS, [])): selector.AreaSelector(selector.AreaSelectorConfig(multiple=True)),
                vol.Optional(OPT_LABELS, default=o.get(OPT_LABELS, [])): selector.LabelSelector(selector.LabelSelectorConfig(multiple=True)),
                vol.Optional(OPT_ENTITIES, default=o.get(OPT_ENTITIES, [])): selector.EntitySelector(selector.EntitySelectorConfig(multiple=True)),
                vol.Optional(OPT_COMMANDS, default=o.get(OPT_COMMANDS, False)): selector.BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
