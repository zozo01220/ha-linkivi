"""Réparations de Linkivi (§310) : « Redémarrage nécessaire » se répare en redémarrant Home Assistant, après confirmation."""

from __future__ import annotations

from typing import Any

from homeassistant import data_entry_flow
from homeassistant.components.repairs import RepairsFlow
from homeassistant.core import HomeAssistant

from .update_check import ISSUE_RESTART


class RestartFlow(RepairsFlow):
    """Une seule étape : confirmer, puis Home Assistant redémarre."""

    def __init__(self, versions: dict[str, Any]) -> None:
        self._versions = {"loaded": str(versions.get("loaded", "")), "disk": str(versions.get("disk", ""))}

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> data_entry_flow.FlowResult:
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None) -> data_entry_flow.FlowResult:
        if user_input is not None:
            await self.hass.services.async_call("homeassistant", "restart", blocking=False)
            return self.async_create_entry(data={})
        return self.async_show_form(step_id="confirm", description_placeholders=self._versions)


async def async_create_fix_flow(hass: HomeAssistant, issue_id: str, data: dict[str, Any] | None) -> RepairsFlow:
    if issue_id == ISSUE_RESTART:
        return RestartFlow(data or {})
    raise ValueError(f"Réparation inconnue : {issue_id}")
