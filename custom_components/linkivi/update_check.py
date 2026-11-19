"""Redémarrage nécessaire (§310) : après une mise à jour par HACS, les nouveaux fichiers sont sur le disque mais Home Assistant garde l'ancien code
tant qu'il n'a pas redémarré. On compare la version chargée à celle du manifest.json sur le disque (au démarrage, puis toutes les 5 minutes) ;
si elles diffèrent, une réparation « Redémarrage nécessaire » apparaît dans Paramètres, avec un bouton qui redémarre Home Assistant (repairs.py).
"""

from __future__ import annotations

import json
import logging
from datetime import timedelta
from pathlib import Path

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.loader import async_get_integration

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

ISSUE_RESTART = "restart_required"
CHECK_EVERY = timedelta(minutes=5)
MANIFEST = Path(__file__).parent / "manifest.json"


def _disk_version() -> str | None:
    try:
        return str(json.loads(MANIFEST.read_text(encoding="utf-8")).get("version") or "") or None
    except (OSError, ValueError):
        return None


async def async_watch_updates(hass: HomeAssistant) -> None:
    """À appeler une fois (async_setup) : retire une ancienne alerte, puis surveille le disque."""
    loaded = str((await async_get_integration(hass, DOMAIN)).version or "")

    async def check(_now=None) -> None:
        disk = await hass.async_add_executor_job(_disk_version)
        if disk and loaded and disk != loaded:
            ir.async_create_issue(
                hass,
                DOMAIN,
                ISSUE_RESTART,
                is_fixable=True,
                is_persistent=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=ISSUE_RESTART,
                translation_placeholders={"loaded": loaded, "disk": disk},
                data={"loaded": loaded, "disk": disk},   # repris par la fenêtre de réparation (repairs.py)
            )
        else:
            ir.async_delete_issue(hass, DOMAIN, ISSUE_RESTART)

    await check()
    unsub = async_track_time_interval(hass, check, CHECK_EVERY)

    @callback
    def _stop(_event=None) -> None:
        unsub()

    hass.bus.async_listen_once("homeassistant_stop", _stop)
