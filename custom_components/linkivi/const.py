"""Constantes de l'intégration Linkivi."""

from datetime import timedelta
from typing import Any

DOMAIN = "linkivi"

# Carte personnalisée « Écran Linkivi » (www/linkivi-screen-card.js, §351 : un écran par carte), publiée sous /linkivi/ et chargée par l'interface.
CARD_FILE = "linkivi-screen-card.js"
CARD_URL = f"/{DOMAIN}/{CARD_FILE}"
CARD_VERSION = "3.0.0"

# L'API publique de Linkivi (§154). L'état arrive en direct par le canal temps réel (§299) ;
# la relecture complète n'est plus qu'un filet de sécurité (toutes les 5 min).
SCAN_INTERVAL = timedelta(minutes=5)
API_PATH = "/api/v1"
DEFAULT_URL = "https://linkivi.duckdns.org"

# Canal temps réel : WebSocket d'abord ; après 3 échecs de suite, attente longue en HTTPS pendant 5 min, puis nouvel essai du WebSocket.
WS_FAILURES_BEFORE_LONG_POLL = 3
LONG_POLL_PERIOD = 300
RETRY_MIN, RETRY_MAX = 5, 60

# Événement Home Assistant émis pour chaque événement de Linkivi (déclencheurs d'appareil : device_trigger.py).
EVENT = "linkivi_event"
# Événement de Linkivi → type de déclencheur d'un écran
TRIGGERS = {
    "screen.offline": "offline",
    "screen.online": "online",
    "screen.applied": "applied",
    "emergency.acknowledged": "emergency",
}

# Commandes acceptées par POST /screens/{id}/commands (module « Écrans », accès screens:control, tous les plans).
CMD_RESTART_PLAYER = "restart-player"
CMD_REBOOT = "reboot"
CMD_POWER_OFF = "poweroff"
CMD_SCREEN_OFF = "screen-off"
CMD_WAKE = "wake"

DEVICE_LABELS = {
    "windows": "Player Windows",
    "raspberrypi": "Player Raspberry Pi",
    "android": "Player Android",
    "androidtv": "Player Android TV",
    "web": "Player navigateur",
}


def hardware(screen: dict[str, Any]) -> str | None:
    """Matériel de la fiche de l'appareil (§349) : modèle et système remontés par le player (« Raspberry Pi 4 Model B · Raspberry Pi OS 12 »)."""
    return " · ".join(v for v in (screen.get("model"), screen.get("os")) if v) or None


# Actions (services.py) : afficher un message sur des écrans, le retirer. Aspects acceptés par POST /screens/{id}/display.
SERVICE_SHOW_MESSAGE = "show_message"
SERVICE_SHOW_COUNTDOWN = "show_countdown"
SERVICE_SHOW_MEDIAPLAYER = "show_mediaplayer_playing"
MUSIC_TAG = "music"   # étiquette par défaut de la musique en cours (§351) : le morceau suivant remplace le précédent
SERVICE_CLEAR_DISPLAY = "clear_display"
SERVICE_SHOW_LIST = "show_list"
SERVICE_START_EMERGENCY = "start_emergency"
SERVICE_END_EMERGENCY = "end_emergency"
LOOKS = ["information", "attention"]
# Places d'un message (§309) : plein écran, bandeau, ou carte dans un coin (la diffusion continue) ; coins possibles.
# « banner » (ancien bandeau unique) reste accepté pour les automatisations existantes, mais n'est plus proposé dans les listes
PLACES = ["full", "banner", "banner_top", "banner_bottom", "corner"]
PLACES_SHOWN = ["full", "banner_top", "banner_bottom", "corner"]
CORNERS = ["bottom_right", "bottom_left", "top_right", "top_left"]
# Image « En direct » d'une caméra : nouvelle image toutes les 2 s pendant l'affichage.
LIVE_IMAGE_SECONDS = 2
MAX_IMAGE_BYTES = 3_000_000

# Écrans suivis (§337) : seuls ces écrans deviennent des appareils ; les autres sont proposés dans Paramètres › Appareils et services › Découvertes.
# Rangés dans entry.data (le parcours d'options réécrit toutes les options) : écrans suivis, écrans déjà vus une fois.
CONF_SCREENS = "screens"
CONF_SEEN = "seen_screens"
# Option : un écran jamais vu devient tout de suite un appareil, sans passer par Découvertes (comportement d'avant la 1.12).
OPT_AUTO_ADD = "auto_add_screens"
DISCOVERY_PREFIX = "screen_"
