"""Ajout de Linkivi (§299, lot 1) : avec un code à vérifier dans Linkivi (proposé), ou en collant une clé d'API (avancé)."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import SOURCE_REAUTH, ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import LinkivApi, LinkivAuthError, LinkivError, clean_url, pair_start, pair_token
from .const import DEFAULT_URL, DOMAIN


class LinkivConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._url = DEFAULT_URL
        self._pair: dict[str, Any] | None = None
        self._task: asyncio.Task[dict[str, Any] | None] | None = None
        self._result: dict[str, Any] | None = None
        self._failure = "expired"

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
