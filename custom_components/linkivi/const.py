"""Constantes de l'intégration Linkivi."""

from datetime import timedelta

DOMAIN = "linkivi"

# Carte personnalisée « Écrans Linkivi » (www/linkivi-screens-card.js), publiée sous /linkivi/ et chargée par l'interface.
CARD_FILE = "linkivi-screens-card.js"
CARD_URL = f"/{DOMAIN}/{CARD_FILE}"
CARD_VERSION = "2.0.1"

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

# Actions (services.py) : afficher un message sur des écrans, le retirer. Aspects acceptés par POST /screens/{id}/display.
SERVICE_SHOW_MESSAGE = "show_message"
SERVICE_CLEAR_DISPLAY = "clear_display"
SERVICE_SHOW_LIST = "show_list"
SERVICE_START_EMERGENCY = "start_emergency"
SERVICE_END_EMERGENCY = "end_emergency"
LOOKS = ["information", "attention"]
# Places d'un message (§309) : plein écran, bandeau, ou carte dans un coin (la diffusion continue) ; coins possibles.
PLACES = ["full", "banner", "corner"]
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
