/*
 * Carte Home Assistant « Écrans Linkivi » (linkivi-screens-card), version 2 (§305, maquette maquettes/ha-carte-ecrans-v2.html).
 * Trouve seule les écrans de l'intégration Linkivi (entités de la plateforme « linkivi », groupées par appareil) et les pilote :
 * interrupteur Écran, redémarrage du player, redémarrage et extinction de l'appareil ; depuis la v2 : liste diffusée, aperçu du direct,
 * fenêtre d'un écran, alerte d'urgence. Aucun nom d'entité à écrire.
 * Deux styles : « cards » (chaque écran est une petite télé) et « list » (lignes givrées sur un fond dégradé).
 * Servie par l'intégration (/linkivi/linkivi-screens-card.js) : chargée toute seule, ou déclarée en ressource « module JavaScript ».
 * Sans dépendance : élément natif + shadow DOM.
 */
const CARD_VERSION = "2.0.1";

const TEXTS = {
  fr: {
    title: "Écrans Linkivi",
    summary: (on, off) => `${on} en ligne${off ? ` · ${off} hors ligne` : ""}`,
    none: "Aucun écran Linkivi trouvé. Ajoutez l'intégration Linkivi (Paramètres › Appareils et services).",
    allOn: "Tout allumer", allOff: "Tout éteindre",
    screenOn: "Écran allumé", screenOff: "Écran éteint", sleep: "En veille", turnOn: "Allumer l'écran", turnOff: "Éteindre l'écran",
    asleep: "en veille", offline: "Hors ligne", offlineSince: (d) => `Hors ligne depuis ${d}`, since: (d) => `depuis ${d}`,
    restartPlayer: "Redémarrer le player", restartDevice: "Redémarrer l'appareil", powerOffDevice: "Éteindre l'appareil…",
    pendingPlayer: "Redémarrage du player…", pendingReboot: "Redémarrage de l'appareil…", pendingPoweroff: "Extinction de l'appareil…",
    confirmReboot: (n) => `Redémarrer « ${n} » ?`, confirmRebootText: "L'appareil sera hors ligne quelques minutes, puis Linkivi reprend l'affichage.", rebootGo: "Redémarrer",
    confirmOff: (n) => `Éteindre « ${n} » ?`, confirmOffText: "Linkivi ne pourra pas le rallumer : il faudra appuyer sur son bouton ou remettre le courant.", offGo: "Éteindre",
    cancel: "Annuler", close: "Fermer", more: "Commandes de l'appareil", failed: (m) => `Linkivi : ${m}`,
    minutes: (n) => `${n} min`, hours: (n) => `${n} h`, days: (n) => `${n} j`,
    // v2
    playlist: "Liste diffusée", noPlaylist: "Aucune liste", choose: "Changer la liste diffusée",
    played: (l, n) => `« ${l} » diffusée sur « ${n} »`, undo: "Annuler",
    preview: "Aperçu du direct", refresh: "Actualiser", updatedAt: (h) => `Mis à jour à ${h}`, noPreview: "Pas d'aperçu pour ce player",
    lastImage: "Dernière image", state: "État", lastSeen: "Dernière connexion", now: "à l'instant", ago: (d) => `il y a ${d}`,
    states: { online: "En ligne", offline: "Hors ligne", updating: "Mise à jour", asleep: "En veille", paused: "En pause" },
    noCtl: "Ni aperçu du direct ni commandes pour cet écran.",
    urgKicker: "Alerte d'urgence en cours", urgMore: (n) => ` (+${n})`, endAlert: "Lever l'alerte",
    confirmEnd: "Lever l'alerte d'urgence ?", confirmEndText: "La diffusion reprend tout de suite sur les écrans concernés.", endGo: "Lever l'alerte",
    startAlert: "Déclencher une alerte…", alertTitle: "Déclencher une alerte d'urgence", alertName: "Titre (40 caractères)", alertMsg: "Message (facultatif)",
    alertOn: (n) => n ? `Sur les ${n} écrans de cette carte, en plein écran rouge, jusqu'à ce qu'on la lève.` : "Sur tous les écrans, en plein écran rouge, jusqu'à ce qu'on la lève.",
    hold: "Maintenir pour déclencher", menu: "Plus",
    ed: { title: "Titre", style: "Style", screens: "Écrans (vide : tous)", show_player_restart: "Redémarrer le player", show_device_actions: "Commandes de l'appareil (⋮)",
      show_group_buttons: "Tout allumer / Tout éteindre", hide_offline: "Masquer les écrans hors ligne", accent_color: "Couleur d'accent (ex. #2a86ee, facultatif)",
      show_playlist: "Liste diffusée", show_preview: "Aperçu du direct", preview_interval: "Aperçu : nouvelle image toutes les (min)",
      show_emergency: "Alerte d'urgence (bandeau et menu)", emergency_for_all: "Tout le monde peut déclencher ou lever l'alerte",
      list: "Liste (verre)", cards: "Cartes (télés)" },
  },
  en: {
    title: "Linkivi screens",
    summary: (on, off) => `${on} online${off ? ` · ${off} offline` : ""}`,
    none: "No Linkivi screen found. Add the Linkivi integration (Settings › Devices & services).",
    allOn: "All on", allOff: "All off",
    screenOn: "Screen on", screenOff: "Screen off", sleep: "Asleep", turnOn: "Turn the screen on", turnOff: "Turn the screen off",
    asleep: "asleep", offline: "Offline", offlineSince: (d) => `Offline for ${d}`, since: (d) => `for ${d}`,
    restartPlayer: "Restart player", restartDevice: "Restart device", powerOffDevice: "Power off device…",
    pendingPlayer: "Restarting the player…", pendingReboot: "Restarting the device…", pendingPoweroff: "Powering off…",
    confirmReboot: (n) => `Restart “${n}”?`, confirmRebootText: "The device will be offline for a few minutes, then Linkivi resumes the display.", rebootGo: "Restart",
    confirmOff: (n) => `Power off “${n}”?`, confirmOffText: "Linkivi cannot turn it back on: someone must press its button or restore power.", offGo: "Power off",
    cancel: "Cancel", close: "Close", more: "Device commands", failed: (m) => `Linkivi: ${m}`,
    minutes: (n) => `${n} min`, hours: (n) => `${n} h`, days: (n) => `${n} d`,
    playlist: "Playlist", noPlaylist: "No playlist", choose: "Change the playlist",
    played: (l, n) => `“${l}” now playing on “${n}”`, undo: "Undo",
    preview: "Live preview", refresh: "Refresh", updatedAt: (h) => `Updated at ${h}`, noPreview: "No preview for this player",
    lastImage: "Last image", state: "Status", lastSeen: "Last seen", now: "just now", ago: (d) => `${d} ago`,
    states: { online: "Online", offline: "Offline", updating: "Updating", asleep: "Asleep", paused: "Paused" },
    noCtl: "No live preview or commands for this screen.",
    urgKicker: "Emergency alert in progress", urgMore: (n) => ` (+${n})`, endAlert: "End the alert",
    confirmEnd: "End the emergency alert?", confirmEndText: "The playlist resumes at once on the screens concerned.", endGo: "End the alert",
    startAlert: "Start an alert…", alertTitle: "Start an emergency alert", alertName: "Title (40 characters)", alertMsg: "Message (optional)",
    alertOn: (n) => n ? `On the ${n} screens of this card, red full screen, until someone ends it.` : "On every screen, red full screen, until someone ends it.",
    hold: "Hold to start", menu: "More",
    ed: { title: "Title", style: "Style", screens: "Screens (empty: all)", show_player_restart: "Restart player", show_device_actions: "Device commands (⋮)",
      show_group_buttons: "All on / All off", hide_offline: "Hide offline screens", accent_color: "Accent colour (e.g. #2a86ee, optional)",
      show_playlist: "Playlist", show_preview: "Live preview", preview_interval: "Preview: new image every (min)",
      show_emergency: "Emergency alert (banner and menu)", emergency_for_all: "Everyone can start or end the alert",
      list: "List (glass)", cards: "Cards (screens)" },
  },
};

const ICON = {
  tv: '<svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/></svg>',
  tablet: '<svg viewBox="0 0 24 24"><rect x="6" y="2.5" width="12" height="19" rx="2.5"/><path d="M11 18.5h2"/></svg>',
  pi: '<svg viewBox="0 0 24 24"><rect x="3" y="6" width="18" height="12" rx="2"/><path d="M7 10v4M11 10v4M15 11h2M15 14h2"/></svg>',
  monitor: '<svg viewBox="0 0 24 24"><rect x="2.5" y="4" width="19" height="12.5" rx="1.5"/><path d="M8 20.5h8M12 16.5v4"/></svg>',
  globe: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.7 2.6 2.7 15.4 0 18M12 3c-2.7 2.6-2.7 15.4 0 18"/></svg>',
  moon: '<svg viewBox="0 0 24 24"><path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/></svg>',
  cloud: '<svg viewBox="0 0 24 24"><path d="M3 3l18 18"/><path d="M17.5 17.5H7a4 4 0 0 1-.6-7.95M9 5.5a6 6 0 0 1 10 4.5 3.5 3.5 0 0 1 2 3"/></svg>',
  restart: '<svg viewBox="0 0 24 24"><path d="M20 12a8 8 0 1 1-2.6-5.9"/><path d="M20 4v5h-5"/></svg>',
  restartAlert: '<svg viewBox="0 0 24 24"><path d="M20 12a8 8 0 1 1-2.6-5.9"/><path d="M20 4v5h-5"/><path d="M12 8.5v4M12 15.5v.01"/></svg>',
  power: '<svg viewBox="0 0 24 24"><path d="M12 3v8"/><path d="M6.3 6.8a8 8 0 1 0 11.4 0"/></svg>',
  dots: '<svg viewBox="0 0 24 24" class="fill"><circle cx="12" cy="5" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="12" cy="19" r="1.6"/></svg>',
  list: '<svg viewBox="0 0 24 24"><path d="M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01"/></svg>',
  chevron: '<svg viewBox="0 0 24 24" class="cv"><path d="M6 9l6 6 6-6"/></svg>',
  alert: '<svg viewBox="0 0 24 24"><path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18v.01"/></svg>',
  close: '<svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg>',
  pause: '<svg viewBox="0 0 24 24"><path d="M9 5v14M15 5v14"/></svg>',
  info: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8v.01"/></svg>',
};

// Rôle de chaque entité de l'intégration, d'après sa clé de traduction (repli : la fin de son identifiant)
const ROLE_BY_KEY = {
  online: "online", screen: "sw", restart_player: "player", reboot: "reboot", power_off: "poweroff",
  playlist: "playlist", state: "state", last_seen: "seen", preview: "cam", emergency: "urg",
};
const PENDING_MS = { player: 20000, reboot: 120000, poweroff: 60000 };
const HOLD_MS = 1500;      // appui maintenu pour déclencher une alerte, comme dans le back-office de Linkivi
const UNDO_MS = 10000;     // bulle « Annuler » après un changement de liste

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/** L'icône d'un écran d'après le modèle que l'intégration donne à l'appareil (« Player Android TV », « Player Raspberry Pi »…). */
const deviceIcon = (model) => /tv/i.test(model) ? ICON.tv : /android/i.test(model) ? ICON.tablet : /raspberry/i.test(model) ? ICON.pi
  : /windows/i.test(model) ? ICON.monitor : /navigateur|web|browser/i.test(model) ? ICON.globe : ICON.tv;

const CSS = `:host{display:block;--lk:#2a86ee;--lk-ok:var(--success-color,#43a047);--lk-warn:var(--warning-color,#ffa726);--lk-off:var(--disabled-color,#9e9e9e);
  --lk-chip:var(--secondary-background-color,rgba(127,127,127,.15));--lk-text:var(--primary-text-color);--lk-sec:var(--secondary-text-color);
  --lk-div:var(--divider-color,rgba(127,127,127,.3));--lk-danger:var(--error-color,#d32f2f);--lk-card:var(--ha-card-background,var(--card-background-color,#fff))}
ha-card{display:block;overflow:visible;position:relative}
svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;pointer-events:none}
svg.fill{fill:currentColor;stroke:none}
button{font:inherit;color:inherit;cursor:pointer}
.hd{display:flex;align-items:center;gap:14px;padding:16px 18px 10px;flex-wrap:wrap}
.hd .t{font-size:19px;font-weight:600;letter-spacing:-.01em;line-height:1.15;color:var(--lk-text)}
.hd .s{font-size:12.5px;color:var(--lk-sec)}
.hd .sp{flex:1}
.ring{width:46px;height:46px;border-radius:50%;background:conic-gradient(var(--lk-ok) calc(var(--v,0)*1%),var(--lk-chip) 0);display:grid;place-items:center;flex:none}
.ring::before{content:"";width:34px;height:34px;border-radius:50%;background:var(--lk-card);grid-area:1/1}
.ring b{grid-area:1/1;font-size:13px;font-weight:600;z-index:1;color:var(--lk-text)}
.chip{border:0;background:var(--lk-chip);color:var(--lk-text);border-radius:16px;padding:6px 12px;font-size:12.5px}
.chip:hover{filter:brightness(.95)}
.ib{width:34px;height:34px;border:0;border-radius:50%;background:color-mix(in srgb,var(--lk-text) 8%,transparent);color:var(--lk-text);display:inline-flex;align-items:center;justify-content:center;padding:0;flex:none}
.ib:hover:not(:disabled){background:color-mix(in srgb,var(--lk-text) 14%,transparent)}
.ib:disabled{opacity:.4;cursor:default}
.empty{padding:16px 18px 18px;color:var(--lk-sec)}
.n{font-weight:600;line-height:1.2;color:var(--lk-text);min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.d{font-size:12px;color:var(--lk-sec);line-height:1.3;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tx{min-width:0}
.sp{flex:1}
.spin{width:12px;height:12px;border:2px solid var(--lk-div);border-top-color:var(--lk-warn);border-radius:50%;display:inline-block;vertical-align:-2px;animation:r 1s linear infinite}
@keyframes r{to{transform:rotate(360deg)}}
@keyframes p{70%{box-shadow:0 0 0 7px rgba(125,255,180,0)}100%{box-shadow:0 0 0 0 rgba(125,255,180,0)}}
.pop{position:absolute;right:10px;z-index:5;min-width:220px;background:var(--card-background-color,#fff);border:1px solid var(--lk-div);border-radius:10px;box-shadow:0 6px 22px rgba(0,0,0,.3);padding:4px}
.pop button{display:flex;width:100%;gap:10px;align-items:center;border:0;background:none;border-radius:6px;padding:9px 12px;font-size:13.5px;text-align:left}
.pop button:hover{background:var(--lk-chip)}
.pop .dg{color:var(--lk-danger)}
.pop hr{border:0;border-top:1px solid var(--lk-div);margin:4px 0}

/* ── style « list » : lignes givrées sur un fond dégradé ── */
ha-card.glass{background:radial-gradient(120% 90% at 0% 0%,color-mix(in srgb,var(--lk) 34%,transparent),transparent 60%),radial-gradient(90% 80% at 100% 100%,color-mix(in srgb,var(--lk-ok) 22%,transparent),transparent 60%),var(--lk-card)}
.li{display:flex;flex-direction:column;gap:8px;padding:4px 14px 16px}
.r{display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:14px;background:color-mix(in srgb,var(--lk-text) 6%,transparent);border:1px solid color-mix(in srgb,var(--lk-text) 10%,transparent);backdrop-filter:blur(8px);position:relative}
.r.out .n{color:var(--lk-sec)}
.av{width:40px;height:40px;border-radius:12px;display:grid;place-items:center;flex:none;background:color-mix(in srgb,var(--lk-ok) 20%,transparent);color:var(--lk-ok);box-shadow:inset 0 0 0 1.5px color-mix(in srgb,var(--lk-ok) 55%,transparent)}
.av.sleep{background:color-mix(in srgb,var(--lk) 16%,transparent);color:var(--lk);box-shadow:inset 0 0 0 1.5px color-mix(in srgb,var(--lk) 45%,transparent)}
.av.busy{background:color-mix(in srgb,var(--lk-warn) 20%,transparent);color:var(--lk-warn);box-shadow:inset 0 0 0 1.5px color-mix(in srgb,var(--lk-warn) 55%,transparent)}
.av.off{background:var(--lk-chip);color:var(--lk-off);box-shadow:inset 0 0 0 1.5px var(--lk-div)}
.pill{width:46px;height:26px;border-radius:13px;border:0;padding:0;background:var(--lk);position:relative;flex:none;box-shadow:0 0 14px color-mix(in srgb,var(--lk) 55%,transparent)}
.pill::after{content:"";position:absolute;top:3px;left:23px;width:20px;height:20px;border-radius:50%;background:#fff;transition:left .15s}
.pill.off{background:var(--lk-off);box-shadow:none}.pill.off::after{left:3px}
.pill:disabled{opacity:.45;cursor:default}
.r .pop{top:56px}
.r.open,.it.open{z-index:6}   /* la ligne dont le menu est ouvert passe au-dessus des suivantes (chacune a son propre empilement) */

/* ── style « cards » : chaque écran est une petite télé ── */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:16px 14px;padding:6px 18px 18px}
.it{position:relative;min-width:0}
.tv{position:relative;aspect-ratio:16/9;border-radius:9px;background:#05070a;border:3px solid #0a0c10;box-shadow:0 0 0 1px rgba(255,255,255,.08),0 6px 14px rgba(0,0,0,.3);overflow:hidden;color:#fff}
.tv.on{background:linear-gradient(135deg,var(--lk) 0%,color-mix(in srgb,var(--lk) 55%,#0b1f3a) 55%,#0b1f3a 100%);box-shadow:0 0 0 1px rgba(255,255,255,.1),0 8px 22px color-mix(in srgb,var(--lk) 45%,transparent)}
.tv.on::after{content:"";position:absolute;inset:0;background:linear-gradient(115deg,rgba(255,255,255,.22) 0,rgba(255,255,255,0) 38%)}
.tv.sleep{background:#06080b}
.tv.off{background:repeating-linear-gradient(135deg,#20262c 0 8px,#1a1f24 8px 16px)}
.tv .in{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;z-index:1;text-align:center;padding:6px}
.tv .in b{font-size:11.5px;font-weight:600;letter-spacing:.02em}
.tv .in span{font-size:10px;opacity:.8}
.tv .in svg{width:22px;height:22px;opacity:.9}
.tv .live{position:absolute;top:7px;right:8px;width:7px;height:7px;border-radius:50%;background:#7dffb4;box-shadow:0 0 0 0 rgba(125,255,180,.7);animation:p 2s infinite;z-index:2}
.tv .big{width:20px;height:20px;border:2px solid rgba(255,255,255,.3);border-top-color:#ffb34d;border-radius:50%;animation:r 1s linear infinite}
.stand{height:5px;width:34%;margin:0 auto;background:#0a0c10;border-radius:0 0 4px 4px}
.cap{display:flex;align-items:center;gap:6px;margin-top:8px}
.cap .n{white-space:normal;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.cap .ib{width:30px;height:30px}.cap .ib svg{width:16px;height:16px}
.cap .pw.on{background:var(--lk);color:#fff}
.it .pop{top:calc(100% - 2px)}

/* ── confirmation ── */
.ov{position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;padding:16px}
.dlg{background:var(--card-background-color,#fff);color:var(--lk-text);border-radius:14px;box-shadow:0 8px 32px rgba(0,0,0,.4);width:340px;max-width:100%;padding:20px}
.dlg .t{font-size:17px;font-weight:500;margin-bottom:8px}
.dlg p{margin:0 0 16px;color:var(--lk-sec);font-size:14px}
.dlg .f{display:flex;justify-content:flex-end;gap:8px}
.dlg .f button{border:0;border-radius:18px;padding:8px 14px;font-size:14px;background:var(--lk-chip)}
.dlg .f .go{background:var(--lk);color:#fff}.dlg .f .go.dg{background:var(--lk-danger)}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
/* la télé et la ligne s'ouvrent au clic : boutons natifs, anneau de focus à l'accent */
button.tv{display:block;width:100%;padding:0;text-align:inherit;cursor:pointer}
button.tv:hover{filter:brightness(1.08)}
button.tv:focus-visible,.pl:focus-visible,.r .hit:focus-visible,.plc:focus-visible{outline:2px solid var(--lk);outline-offset:2px}
/* aperçu du direct : l'image remplace le dessin quand l'écran est allumé (en vrai : <img class="shot" src="/api/camera_proxy/…">) */
.tv .shot{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0}
.tv.on.has-shot{background:#05070a}
.tv.on.has-shot::after{background:linear-gradient(115deg,rgba(255,255,255,.12) 0,rgba(255,255,255,0) 30%);z-index:1}
.tv .scrim{position:absolute;inset:0;background:rgba(0,0,0,.55);z-index:1}
.tv.has-shot .in{z-index:2}
/* liste diffusée : petit lien sous le nom */
.pl{display:inline-flex;align-items:center;gap:4px;max-width:100%;border:0;background:none;padding:2px 6px 2px 4px;margin:1px 0 0 -4px;border-radius:6px;font-size:12px;color:var(--lk-sec);line-height:1.3;min-width:0}
.pl svg{width:13px;height:13px;flex:none}
.pl .lb{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pl .cv{width:12px;height:12px;opacity:.7}
.pl:hover{background:var(--lk-chip);color:var(--lk-text)}
.pl.none .lb{font-style:italic}
.cap .tx{flex:1}
/* style « list » : la ligne entière ouvre la fenêtre (bouton .hit sous les commandes) */
.r .hit{position:absolute;inset:0;border:0;background:none;border-radius:14px;padding:0;z-index:0}
.r>*:not(.hit){position:relative;z-index:1}
.r .tx{pointer-events:none}.r .tx .pl{pointer-events:auto}
.r .d .pl{margin:0 0 0 -4px;padding-top:0;padding-bottom:0}
.r .d .st{margin-right:2px}
/* vignette : le médaillon s'élargit au format 16:9 quand la carte montre des aperçus */
.av.wide{width:64px;height:36px;border-radius:9px}
.av.wide svg{width:17px;height:17px}
.th{position:relative;width:64px;height:36px;border-radius:9px;overflow:hidden;flex:none;background:#05070a;box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--lk-text) 14%,transparent)}
.th .dot{position:absolute;right:4px;top:4px;width:7px;height:7px;border-radius:50%;background:#7dffb4;z-index:2;box-shadow:0 0 0 1.5px rgba(0,0,0,.45)}
.th .scrim{position:absolute;inset:0;background:rgba(0,0,0,.55);z-index:1;display:grid;place-items:center}
.th .scrim .spin{border-color:rgba(255,255,255,.3);border-top-color:var(--lk-warn)}
/* sans commandes (écran qui n'en a pas) : la liste diffusée passe à droite, en pastille */
.plc{display:inline-flex;align-items:center;gap:6px;border:0;background:color-mix(in srgb,var(--lk-text) 8%,transparent);color:var(--lk-text);border-radius:16px;padding:6px 8px 6px 11px;font-size:12.5px;max-width:46%;flex:none;min-width:0}
.plc svg{width:14px;height:14px;flex:none}.plc .cv{width:13px;height:13px;opacity:.7}
.plc .lb{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.plc:hover{background:color-mix(in srgb,var(--lk-text) 14%,transparent)}
/* bandeau d'urgence, en tête de carte */
.urg{display:flex;align-items:center;gap:12px;padding:10px 12px 10px 16px;background:var(--lk-danger);color:#fff;border-radius:calc(var(--ha-card-border-radius,12px) - 1px) calc(var(--ha-card-border-radius,12px) - 1px) 0 0}
.urg>svg{width:22px;height:22px;flex:none;animation:u 1.6s ease-in-out infinite}
@keyframes u{50%{opacity:.45}}
.urg .k{font-size:11.5px;opacity:.9;letter-spacing:.02em;line-height:1.2}
.urg .tt{font-size:15px;font-weight:600;line-height:1.25;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.urg .tx{flex:1}
.urg button{border:0;border-radius:18px;padding:7px 14px;background:#fff;color:var(--lk-danger);font-size:13px;font-weight:500;flex:none}
.hd .pop{top:58px}
/* fenêtre d'un écran, au style des fenêtres de Home Assistant (ha-dialog) */
.hdlg{background:var(--card-background-color,#fff);color:var(--lk-text);border-radius:24px;width:540px;max-width:100%;box-shadow:0 8px 32px rgba(0,0,0,.4);position:relative;padding-bottom:8px}
.hdlg .dh{display:flex;align-items:center;gap:6px;padding:12px 12px 6px}
.hdlg .dh .ib{background:none}
.hdlg .dh .ib:hover{background:color-mix(in srgb,var(--lk-text) 8%,transparent)}
.hdlg .dh .ttl{font-size:20px;font-weight:400;line-height:1.2}
.hdlg .dh .sub{font-size:13px;color:var(--lk-sec)}
.hdlg .dh .pop{top:52px;right:12px}
.hero{position:relative;margin:4px 20px 0;aspect-ratio:16/9;border-radius:12px;overflow:hidden;background:#05070a;color:#fff}
.hero.old .shot,.hero.old .fk{filter:grayscale(1) brightness(.55)}
.hero .meta,.hero .re{position:absolute;bottom:10px;z-index:3;display:inline-flex;align-items:center;gap:6px;background:rgba(0,0,0,.55);color:#fff;border:0;border-radius:16px;padding:5px 11px;font-size:12.5px;backdrop-filter:blur(6px)}
.hero .meta{left:10px}.hero .re{right:10px}
.hero .re svg{width:15px;height:15px}
.hero .re:disabled{opacity:.55;cursor:default}
.hero .meta .spin{border-color:rgba(255,255,255,.3);border-top-color:var(--lk-warn)}
.hero .msg{position:absolute;inset:0;z-index:2;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;font-size:13px}
.hero .msg svg{width:26px;height:26px}
.hdlg .bd{padding:16px 20px 8px;display:flex;flex-direction:column;gap:14px}
.facts{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.fact{background:color-mix(in srgb,var(--lk-text) 5%,transparent);border-radius:12px;padding:9px 12px}
.fact .k{font-size:12px;color:var(--lk-sec)}
.fact .v{font-size:14px;display:flex;align-items:center;gap:7px;margin-top:2px}
.dot{width:8px;height:8px;border-radius:50%;flex:none;background:var(--lk-ok)}
.dot.sleep{background:var(--lk)}.dot.busy{background:var(--lk-warn)}.dot.off{background:var(--lk-off)}
/* champ « rempli » de Home Assistant (ha-select, ha-textfield) */
.fld{position:relative;background:color-mix(in srgb,var(--lk-text) 6%,transparent);border-radius:4px 4px 0 0;border-bottom:1px solid var(--lk-sec);padding:8px 40px 7px 14px;min-height:56px;display:flex;flex-direction:column;justify-content:center}
.fld .k{font-size:12px;color:var(--lk-sec)}
.fld .v{font-size:16px;line-height:1.35}
.fld .v.ph{color:var(--lk-sec)}
.fld>svg{position:absolute;right:12px;top:50%;margin-top:-9px;color:var(--lk-sec)}
.fld.focus{border-bottom:2px solid var(--lk);padding-bottom:6px}.fld.focus .k{color:var(--lk)}
.fld.area{min-height:88px;justify-content:flex-start;padding-top:10px}
.fld .help{position:absolute;left:14px;bottom:-19px;font-size:11.5px;color:var(--lk-sec)}
.menu{position:absolute;left:0;right:0;top:100%;z-index:6;background:var(--card-background-color,#fff);border-radius:4px;box-shadow:0 6px 22px rgba(0,0,0,.35);padding:6px 0}
.menu div{display:flex;align-items:center;gap:10px;padding:10px 16px;font-size:15px}
.menu div.sel{background:color-mix(in srgb,var(--lk) 14%,transparent);color:var(--lk)}
.menu div svg{width:16px;height:16px;margin-left:auto}
.row2{display:flex;align-items:center;gap:12px;min-height:44px}
.row2>svg{color:var(--lk-sec)}
.row2 .lb{flex:1;font-size:15px}
/* interrupteur de Home Assistant (ha-switch) */
.hsw{width:36px;height:14px;border-radius:7px;background:var(--lk-off);position:relative;flex:none;margin-right:6px;border:0;padding:0}
.hsw::after{content:"";position:absolute;top:-3px;left:-2px;width:20px;height:20px;border-radius:50%;background:#fafafa;box-shadow:0 1px 3px rgba(0,0,0,.4)}
.hsw.on{background:color-mix(in srgb,var(--lk) 50%,transparent)}.hsw.on::after{left:18px;background:var(--lk)}
.hsw:disabled{opacity:.45}
.acts{display:flex;gap:8px;flex-wrap:wrap;padding-top:2px}
.hbtn{border:1px solid var(--lk-div);background:none;color:var(--lk);border-radius:18px;padding:7px 14px;font-size:14px;display:inline-flex;align-items:center;gap:7px}
.hbtn svg{width:16px;height:16px}
.hbtn:disabled{color:var(--lk-off);cursor:default}
.hnote{font-size:12.5px;color:var(--lk-sec);display:flex;gap:7px;align-items:center}
.hnote svg{width:15px;height:15px;flex:none}
/* fenêtre « Déclencher une alerte » : un peu plus large que la confirmation, appui maintenu */
.dlg.wide{width:400px}
.dlg .flds{display:flex;flex-direction:column;gap:12px;margin:4px 0 14px}
.dlg .on-scr{font-size:13px;color:var(--lk-sec);margin:-2px 0 16px;display:flex;gap:7px;align-items:flex-start}
.dlg .on-scr svg{width:16px;height:16px;flex:none;margin-top:1px}
.dlg .f .hold{position:relative;overflow:hidden}
.dlg .f .hold i{position:absolute;left:0;top:0;bottom:0;width:var(--h,0%);background:rgba(255,255,255,.28)}
.dlg .f .hold span{position:relative}
/* bulle d'annulation (toast de Home Assistant) */
.toast{display:flex;align-items:center;gap:18px;background:#323232;color:#fff;border-radius:8px;padding:12px 10px 12px 16px;font-size:14px;box-shadow:0 4px 14px rgba(0,0,0,.35);max-width:420px}
.toast button{border:0;background:none;color:var(--lk);font-weight:500;font-size:14px;padding:6px 8px;border-radius:4px;text-transform:uppercase;letter-spacing:.04em}
.tst{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);z-index:10000}
.fld select,.fld input,.fld textarea{all:unset;font-size:16px;line-height:1.35;width:100%;color:var(--lk-text)}
.fld textarea{min-height:48px;white-space:pre-wrap}
`;

class LinkivScreensCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._pending = {};     // appareil -> { label, until }
    this._optimistic = {};  // appareil -> { on, until }
    this._menu = null;      // appareil dont le menu ⋮ est ouvert ; « hd » : menu de l'en-tête
    this._plmenu = null;    // appareil dont le choix de liste est ouvert
    this._dialog = null;    // fenêtre de confirmation
    this._detail = null;    // appareil dont la fenêtre est ouverte
    this._tick = 0;         // nouvelle image de l'aperçu dans la fenêtre
    this._alert = null;     // fenêtre « Déclencher une alerte » : { title, message }
    this._toast = null;     // bulle « Annuler » : { text, undo, until }
    this._visible = true;
    this._sig = "";
    this._timer = null;
    // un clic hors d'un menu le ferme ; sur le bouton qui l'ouvre, c'est son propre clic qui le referme
    this._onDocClick = (e) => {
      if (!this._menu && !this._plmenu) return;
      const path = e.composedPath();
      if (path.some((el) => el.classList?.contains("pop")) || path.some((el) => ["menu", "hmenu", "pl"].includes(el.dataset?.act))) return;
      this._menu = null; this._plmenu = null;
      this._render(true);
    };
  }

  static getConfigElement() { return document.createElement("linkivi-screens-card-editor"); }
  static getStubConfig() { return { type: "custom:linkivi-screens-card" }; }

  static defaults() {
    return { style: "list", show_player_restart: true, show_device_actions: true, show_group_buttons: true, hide_offline: false,
      show_playlist: true, show_preview: true, preview_interval: 5, show_emergency: true, emergency_for_all: false };
  }

  setConfig(config) {
    this._config = { ...LinkivScreensCard.defaults(), ...config };
    if (!["list", "cards"].includes(this._config.style)) this._config.style = "list";
    this._config.preview_interval = Math.max(1, Math.min(60, Number(this._config.preview_interval) || 5));
    if (this._config.accent_color) this.style.setProperty("--lk", String(this._config.accent_color));
    else this.style.removeProperty("--lk");
    this._sig = "";
    this._render(true);
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  connectedCallback() {
    document.addEventListener("click", this._onDocClick, true);
    // aperçu : une nouvelle image seulement quand la carte est visible (chaque image demande une capture à l'appareil)
    if ("IntersectionObserver" in window && !this._io) {
      this._io = new IntersectionObserver((entries) => { this._visible = entries.some((x) => x.isIntersecting); this._render(); });
      this._io.observe(this);
    }
    this._clock = setInterval(() => this._render(), 30000);   // tranches de l'aperçu, « il y a… »
  }

  disconnectedCallback() {
    document.removeEventListener("click", this._onDocClick, true);
    clearTimeout(this._timer); clearInterval(this._clock); clearInterval(this._detailClock);
    this._io?.disconnect(); this._io = null;
  }

  getCardSize() { return this._config.style === "cards" ? 2 + 2 * Math.ceil(((this._items || []).length || 1) / 3) : 1 + Math.max(1, (this._items || []).length); }
  getGridOptions() { return { columns: 12, min_columns: 6 }; }

  get _t() { return TEXTS[(this._hass?.language || "en").startsWith("fr") ? "fr" : "en"]; }

  /** Déclencher ou lever l'alerte : les administrateurs de Home Assistant, ou tout le monde si l'option le permet. */
  get _canAlert() { return !!(this._hass?.user?.is_admin || this._config.emergency_for_all); }

  /* ── les écrans : les entités de la plateforme linkivi, groupées par appareil ── */
  _discover() {
    const hass = this._hass;
    const byDevice = new Map();
    this._urg = null;
    for (const [eid, reg] of Object.entries(hass.entities || {})) {
      if (reg.platform !== "linkivi" || !reg.device_id || reg.hidden) continue;
      let role = ROLE_BY_KEY[reg.translation_key];
      if (!role) role = eid.startsWith("switch.") ? "sw" : eid.startsWith("select.") ? "playlist" : eid.startsWith("camera.") ? "cam"
        : /urgence|emergency/.test(eid) && eid.startsWith("binary_sensor.") ? "urg" : eid.startsWith("binary_sensor.") ? "online"
        : /redemarrer_le_player$|restart_player$/.test(eid) ? "player" : /redemarrer_l_appareil$|restart_device$/.test(eid) ? "reboot"
        : /eteindre_l_appareil$|power_off/.test(eid) ? "poweroff" : /derniere_connexion$|last_seen$/.test(eid) ? "seen" : /_etat$|_state$|_status$/.test(eid) ? "state" : null;
      if (!role) continue;
      if (role === "urg") { this._urg = eid; continue; }   // appareil « Organisation » : pas un écran
      const s = byDevice.get(reg.device_id) || { id: reg.device_id };
      s[role] = eid;
      byDevice.set(reg.device_id, s);
    }
    const wanted = (this._config.screens || []).map((x) => String(x).toLowerCase());
    const now = Date.now();
    const bucket = Math.floor(now / (this._config.preview_interval * 60000));
    const items = [];
    for (const s of byDevice.values()) {
      if (!s.online) continue;
      const dev = hass.devices?.[s.id];
      s.name = dev?.name_by_user || dev?.name || s.id;
      if (wanted.length && !wanted.includes(s.name.toLowerCase())) continue;
      const online = hass.states[s.online]?.state === "on";
      const swState = hass.states[s.sw]?.state;
      const opt = this._optimistic[s.id];
      s.ctl = !!(s.sw || s.player || s.reboot || s.poweroff || s.cam);
      s.swOn = opt && opt.until > now ? opt.on : swState === "on";
      s.swDisabled = !s.sw || swState === undefined || swState === "unavailable";
      s.isOnline = online;
      s.status = hass.states[s.state]?.state;   // capteur « État » : online, offline, updating, asleep, paused
      s.asleep = s.status ? s.status === "asleep" : swState === "off";
      s.model = (dev?.model || "").replace(/^Player /, "");
      s.area = hass.areas?.[dev?.area_id]?.name || "";
      const pl = hass.states[s.playlist];
      s.plName = pl && !["unknown", "unavailable"].includes(pl.state) ? pl.state : "";
      s.plOptions = pl?.attributes?.options || [];
      const seen = hass.states[s.seen]?.state && !["unknown", "unavailable"].includes(hass.states[s.seen]?.state)
        ? hass.states[s.seen].state : hass.states[s.online]?.attributes?.last_seen;
      s.seenAt = seen || "";
      s.offlineFor = !online && seen ? this._since(seen) : "";
      const p = this._pending[s.id];
      s.pending = p && p.until > now ? p.label : "";
      const pic = hass.states[s.cam]?.attributes?.entity_picture;
      s.pic = s.cam && pic ? pic : "";
      // aperçu dans la carte : écran allumé et en ligne, carte visible, une image par tranche de « preview_interval » minutes
      s.shot = this._config.show_preview && s.pic && online && this._look(s) === "on" && !s.pending && this._visible
        ? `${s.pic}${s.pic.includes("?") ? "&" : "?"}lk=${bucket}` : "";
      if (this._config.hide_offline && !online) continue;
      items.push(s);
    }
    items.sort((a, b) => a.name.localeCompare(b.name, hass.language || "fr", { sensitivity: "base" }));
    return items;
  }

  _since(iso) {
    const t = this._t;
    const m = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
    if (Number.isNaN(m)) return "";
    return m < 60 ? t.minutes(Math.max(1, m)) : m < 2880 ? t.hours(Math.round(m / 60)) : t.days(Math.round(m / 1440));
  }

  /**
   * « on » (allumé), « sleep », « off » (hors ligne) : la classe visuelle d'un écran. D'après le capteur « État » quand il existe ;
   * sans interrupteur, un écran en ligne est allumé (la 1.2 le disait « en veille »).
   */
  _look(s) {
    if (!s.isOnline || s.status === "offline") return "off";
    const opt = this._optimistic[s.id];
    if (opt && opt.until > Date.now()) return opt.on ? "on" : "sleep";
    if (s.status) return s.status === "asleep" || s.status === "paused" ? "sleep" : "on";
    return s.sw ? (s.swOn ? "on" : "sleep") : "on";
  }

  _stateLabel(s) {
    const t = this._t;
    if (s.pending) return s.pending;
    if (!s.isOnline) return s.offlineFor ? t.offlineSince(s.offlineFor) : t.offline;
    return t.states[s.status] || (this._look(s) === "sleep" ? t.sleep : t.states.online);
  }

  /* ── affichage ── */
  _render(force) {
    if (!this._hass || !this._config) return;
    const items = this._discover();
    this._items = items;
    const urg = this._urg ? this._hass.states[this._urg] : null;
    const sig = JSON.stringify([items.map((s) => [s.id, s.name, s.isOnline, s.swOn, s.status, s.swDisabled, s.pending, s.offlineFor, s.model, s.area, s.plName, s.plOptions, s.shot, s.seenAt,
      !!s.player, !!s.reboot, !!s.poweroff, !!s.cam]), urg?.state, urg?.attributes?.emergencies, this._config, this._menu, this._plmenu, !!this._dialog, this._detail, this._tick,
      !!this._alert, this._toast && this._toast.until > Date.now() ? this._toast.text : null, this._hass.language, this._hass.user?.is_admin]);
    if (!force && sig === this._sig) return;
    // la fenêtre « Déclencher une alerte » garde ce qui est en cours de saisie
    const keep = this._alert ? { title: this.shadowRoot.querySelector("#lk-at")?.value ?? this._alert.title, message: this.shadowRoot.querySelector("#lk-am")?.value ?? this._alert.message } : null;
    if (keep) this._alert = keep;
    this._sig = sig;
    this._schedule();

    const t = this._t, c = this._config;
    const online = items.filter((s) => s.isOnline).length;
    const cards = c.style === "cards";
    const body = !items.length ? `<div class="empty">${esc(t.none)}</div>` : cards ? this._cards(items) : this._list(items);
    const group = c.show_group_buttons && items.some((s) => !s.swDisabled)
      ? `<button class="chip" data-act="all-on">${esc(t.allOn)}</button><button class="chip" data-act="all-off">${esc(t.allOff)}</button>` : "";
    const canStart = c.show_emergency && this._urg && this._canAlert && this._hass.services?.linkivi?.start_emergency;
    const hmenu = canStart ? `<button class="ib" data-act="hmenu" title="${esc(t.menu)}" aria-label="${esc(t.menu)}">${ICON.dots}</button>` : "";
    const hpop = this._menu === "hd" ? `<div class="pop"><button class="dg" data-act="alert-open">${ICON.alert}${esc(t.startAlert)}</button></div>` : "";
    this.shadowRoot.innerHTML = `<style>${CSS}</style><ha-card class="${cards ? "" : "glass"}">
      ${this._banner(urg)}
      <div class="hd"><div class="ring" style="--v:${items.length ? Math.round((online / items.length) * 100) : 0}"><b>${online}</b></div>
        <div><div class="t">${esc(c.title || t.title)}</div><div class="s">${esc(t.summary(online, items.length - online))}</div></div><span class="sp"></span>${group}${hmenu}${hpop}</div>
      ${body}${this._detailHtml()}${this._alertHtml()}${this._dialogHtml()}${this._toastHtml()}</ha-card>`;
    this._bind();
  }

  _schedule() {
    clearTimeout(this._timer);
    const now = Date.now();
    const next = [...Object.values(this._pending), ...Object.values(this._optimistic), ...(this._toast ? [this._toast] : [])].map((p) => p.until).filter((u) => u > now);
    if (next.length) this._timer = setTimeout(() => { this._sig = ""; this._render(); }, Math.min(...next) - now + 50);
  }

  /** Bandeau rouge en tête de carte tant qu'une alerte d'urgence est en cours. */
  _banner(urg) {
    if (!this._config.show_emergency || urg?.state !== "on") return "";
    const t = this._t;
    const list = urg.attributes?.emergencies || [];
    const title = list[0]?.title || t.urgKicker;
    return `<div class="urg" role="alert">${ICON.alert}<div class="tx"><div class="k">${esc(t.urgKicker)}</div><div class="tt">${esc(title)}${list.length > 1 ? esc(t.urgMore(list.length - 1)) : ""}</div></div>
      ${this._canAlert && this._hass.services?.linkivi?.end_emergency ? `<button data-act="alert-end">${esc(t.endAlert)}</button>` : ""}</div>`;
  }

  /** Le menu ⋮ (commandes de l'appareil), commun aux deux styles et à la fenêtre. */
  _pop(s, inDetail) {
    if (this._menu !== (inDetail ? "d:" + s.id : s.id)) return "";
    const t = this._t;
    return `<div class="pop">
      ${s.reboot ? `<button data-act="reboot" data-id="${esc(s.id)}">${ICON.restartAlert}${esc(t.restartDevice)}</button>` : ""}
      ${s.reboot && s.poweroff ? "<hr>" : ""}
      ${s.poweroff ? `<button class="dg" data-act="poweroff" data-id="${esc(s.id)}">${ICON.power}${esc(t.powerOffDevice)}</button>` : ""}</div>`;
  }

  /** Choix de la liste diffusée : menu sous le lien (ou la pastille). */
  _plPop(s) {
    if (this._plmenu !== s.id) return "";
    return `<div class="pop">${s.plOptions.map((o, i) => `<button data-act="pick" data-id="${esc(s.id)}" data-v="${i}">${o === s.plName ? "✓ " : ""}${esc(o)}</button>`).join("")}</div>`;
  }

  _plLink(s, chip) {
    const c = this._config, t = this._t;
    if (!c.show_playlist || !s.playlist) return "";
    const label = s.plName || t.noPlaylist;
    const can = s.plOptions.length > 0;
    return `<button class="${chip ? "plc" : "pl"} ${s.plName ? "" : "none"}" data-act="pl" data-id="${esc(s.id)}" ${can ? "" : "disabled"} title="${esc(t.choose)}" aria-label="${esc(t.playlist)} : ${esc(label)}">${ICON.list}<span class="lb">${esc(label)}</span>${can ? ICON.chevron : ""}</button>`;
  }

  _buttons(s) {
    const t = this._t, c = this._config, id = esc(s.id);
    const restart = c.show_player_restart && s.player
      ? `<button class="ib" data-act="player" data-id="${id}" ${s.isOnline && !s.pending ? "" : "disabled"} title="${esc(t.restartPlayer)}" aria-label="${esc(t.restartPlayer)}">${ICON.restart}</button>` : "";
    const more = c.show_device_actions && (s.reboot || s.poweroff)
      ? `<button class="ib" data-act="menu" data-id="${id}" title="${esc(t.more)}" aria-label="${esc(t.more)}">${ICON.dots}</button>` : "";
    return { restart, more };
  }

  /** Style « list » : une ligne givrée par écran ; vignette d'aperçu, ou médaillon dont la couleur donne l'état. Toute la ligne ouvre la fenêtre. */
  _list(items) {
    const t = this._t;
    const wide = this._config.show_preview && items.some((s) => s.pic);
    return `<div class="li">${items.map((s) => {
      const look = this._look(s), id = esc(s.id), b = this._buttons(s);
      const state = s.pending ? "busy" : look === "on" ? "" : look;
      const icon = s.pending ? ICON.restart : look === "off" ? ICON.cloud : look === "sleep" ? (s.status === "paused" ? ICON.pause : ICON.moon) : deviceIcon(s.model);
      const av = s.shot ? `<div class="th"><img class="shot" src="${esc(s.shot)}" alt="" onerror="this.remove()"><i class="dot"></i></div>`
        : `<div class="av ${state} ${wide ? "wide" : ""}">${icon}</div>`;
      const st = s.pending ? `<span class="spin"></span> ${esc(s.pending)}` : look === "on" && (!s.status || s.status === "online") ? "" : `<span class="st">${esc(this._stateLabel(s))}</span>${s.ctl && s.playlist && this._config.show_playlist ? " · " : ""}`;
      const sub = s.ctl ? `${st}${this._plLink(s)}` : (st || esc([s.model, s.area].filter(Boolean).join(" · ")));
      const toggle = s.sw ? `<button class="pill ${s.swOn ? "" : "off"}" data-act="toggle" data-id="${id}" ${s.swDisabled ? "disabled" : ""} title="${esc(s.swOn ? t.turnOff : t.turnOn)}" aria-label="${esc(s.swOn ? t.screenOn : t.screenOff)}"></button>`
        : this._plLink(s, true);   // sans commandes : la liste passe à droite, en pastille
      return `<div class="r ${look === "off" ? "out" : ""} ${this._menu === s.id || this._plmenu === s.id ? "open" : ""}">
        <button class="hit" data-act="open" data-id="${id}" aria-label="${esc(s.name)}"></button>
        ${av}
        <div class="tx"><div class="n">${esc(s.name)}</div><div class="d">${sub}</div></div><span class="sp"></span>
        ${b.restart}${b.more}${toggle}
        ${this._pop(s)}${this._plPop(s)}</div>`;
    }).join("")}</div>`;
  }

  /** Style « cards » : chaque écran est une petite télé ; l'aperçu du direct s'y affiche quand il existe. La télé ouvre la fenêtre. */
  _cards(items) {
    const t = this._t;
    return `<div class="grid">${items.map((s) => {
      const look = this._look(s), id = esc(s.id), b = this._buttons(s);
      let inner = "";
      if (s.pending) inner = `<div class="big"></div><b>${esc(s.pending)}</b>`;
      else if (look === "off") inner = `${ICON.cloud}<b>${esc(t.offline)}</b>${s.offlineFor ? `<span>${esc(t.since(s.offlineFor))}</span>` : ""}`;
      else if (look === "sleep") inner = `${s.status === "paused" ? ICON.pause : ICON.moon}<b>${esc(this._stateLabel(s))}</b>`;
      else if (!s.shot) inner = `${deviceIcon(s.model)}<b>${esc(s.status === "updating" ? t.states.updating : t.screenOn)}</b>`;
      const shot = s.shot ? `<img class="shot" src="${esc(s.shot)}" alt="" onerror="this.remove()">` : "";
      const sub = this._config.show_playlist && s.playlist ? this._plLink(s) : `<div class="d">${esc([s.model, s.area].filter(Boolean).join(" · "))}</div>`;
      const power = s.sw ? `<button class="ib pw ${s.swOn ? "on" : ""}" data-act="toggle" data-id="${id}" ${s.swDisabled ? "disabled" : ""} title="${esc(s.swOn ? t.turnOff : t.turnOn)}" aria-label="${esc(s.swOn ? t.screenOn : t.screenOff)}">${ICON.power}</button>` : "";
      return `<div class="it ${this._menu === s.id || this._plmenu === s.id ? "open" : ""}">
        <button class="tv ${s.pending ? "on" : look} ${s.shot ? "has-shot" : ""}" data-act="open" data-id="${id}" aria-label="${esc(s.name)}">${shot}${look === "on" && !s.pending ? '<i class="live"></i>' : ""}<div class="in">${inner}</div></button><div class="stand"></div>
        <div class="cap"><div class="tx"><div class="n">${esc(s.name)}</div>${sub}</div>
          ${power}${b.restart}${b.more}</div>
        ${this._pop(s)}${this._plPop(s)}</div>`;
    }).join("")}</div>`;
  }

  /** Fenêtre d'un écran : grand aperçu, liste diffusée, état, dernière connexion, commandes. */
  _detailHtml() {
    const s = this._detail ? this._item(this._detail) : null;
    if (!s) return "";
    const t = this._t, id = esc(s.id), look = this._look(s);
    let hero;
    if (s.ctl && s.pic) {
      const url = `${s.pic}${s.pic.includes("?") ? "&" : "?"}lkd=${this._tick}`;
      hero = `<div class="hero ${look === "off" ? "old" : ""}"><img class="shot" src="${esc(url)}" alt="${esc(t.preview)}" data-act="shot-load"
          onerror="this.style.display='none'">
        <span class="meta">${esc(look === "off" ? t.lastImage : this._shotAt ? t.updatedAt(this._shotAt) : t.preview)}</span>
        ${look !== "off" ? `<button class="re" data-act="refresh" ${this._refreshUntil > Date.now() ? "disabled" : ""}>${ICON.restart}${esc(t.refresh)}</button>` : ""}</div>`;
    } else if (s.ctl) hero = `<div class="hero"><div class="msg">${deviceIcon(s.model)}<span>${esc(t.noPreview)}</span></div></div>`;
    else hero = "";
    const pl = this._config.show_playlist && s.playlist
      ? `<label class="fld"><span class="k">${esc(t.playlist)}</span><select data-change="plsel" data-id="${id}" ${s.plOptions.length ? "" : "disabled"}>
          ${s.plName ? "" : `<option value="" selected>${esc(t.noPlaylist)}</option>`}${s.plOptions.map((o) => `<option ${o === s.plName ? "selected" : ""}>${esc(o)}</option>`).join("")}</select></label>` : "";
    const dot = s.pending ? "busy" : look === "on" ? "" : look;
    const facts = `<div class="facts"><div class="fact"><div class="k">${esc(t.state)}</div><div class="v"><i class="dot ${dot}"></i>${esc(this._stateLabel(s))}</div></div>
      <div class="fact"><div class="k">${esc(t.lastSeen)}</div><div class="v">${esc(s.seenAt ? (Date.now() - new Date(s.seenAt).getTime() < 90000 ? t.now : t.ago(this._since(s.seenAt))) : "—")}</div></div></div>`;
    const b = this._buttons(s);
    const sw = s.sw ? `<div class="row2">${ICON.power}<span class="lb">${esc(s.swOn ? t.screenOn : t.screenOff)}</span>
        <button class="hsw ${s.swOn ? "on" : ""}" data-act="toggle" data-id="${id}" ${s.swDisabled ? "disabled" : ""} aria-label="${esc(s.swOn ? t.turnOff : t.turnOn)}"></button></div>` : "";
    const acts = s.player || s.reboot || s.poweroff ? `<div class="acts">
        ${s.player ? `<button class="hbtn" data-act="player" data-id="${id}" ${s.isOnline && !s.pending ? "" : "disabled"}>${ICON.restart}${esc(t.restartPlayer)}</button>` : ""}
        ${s.reboot ? `<button class="hbtn" data-act="reboot" data-id="${id}" ${s.isOnline && !s.pending ? "" : "disabled"}>${ICON.restartAlert}${esc(t.restartDevice)}</button>` : ""}
        ${s.poweroff ? `<button class="hbtn" data-act="poweroff" data-id="${id}" ${s.isOnline && !s.pending ? "" : "disabled"}>${ICON.power}${esc(t.powerOffDevice)}</button>` : ""}</div>` : "";
    const note = s.ctl ? "" : `<div class="hnote">${ICON.info}${esc(t.noCtl)}</div>`;
    void b;
    return `<div class="ov" data-act="detail-bg"><div class="hdlg" role="dialog" aria-modal="true" aria-label="${esc(s.name)}">
      <div class="dh"><button class="ib" data-act="detail-close" aria-label="${esc(t.close)}">${ICON.close}</button>
        <div class="tx"><div class="ttl">${esc(s.name)}</div><div class="sub">${esc([s.model, s.area].filter(Boolean).join(" · "))}</div></div></div>
      ${hero}<div class="bd">${pl}${facts}${sw}${acts}${note}</div></div></div>`;
  }

  /** Fenêtre « Déclencher une alerte » : titre, message, appui maintenu 1,5 s. */
  _alertHtml() {
    if (!this._alert) return "";
    const t = this._t;
    const n = (this._config.screens || []).length ? this._items.length : 0;
    return `<div class="ov" data-act="alert-bg"><div class="dlg wide" role="dialog" aria-modal="true"><div class="t">${esc(t.alertTitle)}</div>
      <div class="flds"><label class="fld"><span class="k">${esc(t.alertName)}</span><input id="lk-at" maxlength="40" value="${esc(this._alert.title)}"></label>
        <label class="fld area"><span class="k">${esc(t.alertMsg)}</span><textarea id="lk-am" maxlength="300">${esc(this._alert.message)}</textarea></label></div>
      <p class="on-scr">${ICON.info}<span>${esc(t.alertOn(n))}</span></p>
      <div class="f"><button data-act="alert-cancel">${esc(t.cancel)}</button><button class="go dg hold" data-hold="alert-go"><i></i><span>${esc(t.hold)}</span></button></div></div></div>`;
  }

  _dialogHtml() {
    const d = this._dialog;
    if (!d) return "";
    const t = this._t;
    return `<div class="ov" data-act="dlg-bg"><div class="dlg" role="dialog" aria-modal="true"><div class="t">${esc(d.title)}</div><p>${esc(d.text)}</p>
      <div class="f"><button data-act="dlg-cancel">${esc(t.cancel)}</button><button class="go ${d.danger ? "dg" : ""}" data-act="dlg-ok">${esc(d.go)}</button></div></div></div>`;
  }

  _toastHtml() {
    const x = this._toast;
    if (!x || x.until <= Date.now()) return "";
    return `<div class="tst"><div class="toast" role="status"><span>${esc(x.text)}</span>${x.undo ? `<button data-act="undo">${esc(this._t.undo)}</button>` : ""}</div></div>`;
  }

  _bind() {
    const root = this.shadowRoot;
    root.querySelectorAll("[data-act]").forEach((el) => {
      if (el.dataset.act === "shot-load") {
        el.addEventListener("load", () => { this._shotAt = new Date().toLocaleTimeString(this._hass.language || "fr", { hour: "2-digit", minute: "2-digit" }); const m = root.querySelector(".hero .meta"); if (m) m.textContent = this._t.updatedAt(this._shotAt); });
        return;
      }
      el.addEventListener("click", (e) => {
        if (/-bg$/.test(el.dataset.act) && e.target !== el) return;
        e.stopPropagation();
        this._act(el.dataset.act, el.dataset.id, el.dataset.v);
      });
    });
    root.querySelectorAll("[data-change]").forEach((el) => el.addEventListener("change", () => {
      const s = this._item(el.dataset.id);
      if (s && el.value) this._choose(s, el.value);
    }));
    root.querySelectorAll("[data-hold]").forEach((el) => {
      let timer = null, start = 0, raf = 0;
      const stop = () => { clearTimeout(timer); cancelAnimationFrame(raf); el.style.setProperty("--h", "0%"); };
      const step = () => { el.style.setProperty("--h", `${Math.min(100, ((Date.now() - start) / HOLD_MS) * 100)}%`); raf = requestAnimationFrame(step); };
      el.addEventListener("pointerdown", (e) => { e.preventDefault(); start = Date.now(); step(); timer = setTimeout(() => { stop(); this._startAlert(); }, HOLD_MS); });
      ["pointerup", "pointerleave", "pointercancel"].forEach((ev) => el.addEventListener(ev, stop));
    });
  }

  _item(id) { return (this._items || []).find((s) => s.id === id); }

  _act(act, id, v) {
    const t = this._t, s = id ? this._item(id) : null;
    switch (act) {
      case "toggle": return s && this._toggle(s, !s.swOn);
      case "all-on": return this._items.filter((x) => !x.swDisabled).forEach((x) => this._toggle(x, true));
      case "all-off": return this._items.filter((x) => !x.swDisabled).forEach((x) => this._toggle(x, false));
      case "player": return s && this._press(s, "player", t.pendingPlayer);
      case "menu": this._plmenu = null; this._menu = this._menu === id ? null : id; return this._render(true);
      case "hmenu": this._plmenu = null; this._menu = this._menu === "hd" ? null : "hd"; return this._render(true);
      case "pl": this._menu = null; this._plmenu = this._plmenu === id ? null : id; return this._render(true);
      case "pick": this._plmenu = null; return s && this._choose(s, s.plOptions[Number(v)]);
      case "open":
        this._detail = id; this._tick = Date.now(); this._shotAt = ""; this._menu = null; this._plmenu = null;
        clearInterval(this._detailClock);
        this._detailClock = setInterval(() => { this._tick = Date.now(); this._render(); }, 60000);   // une capture par minute tant que la fenêtre reste ouverte
        return this._render(true);
      case "detail-close": case "detail-bg": this._detail = null; clearInterval(this._detailClock); return this._render(true);
      case "refresh": this._tick = Date.now(); this._refreshUntil = Date.now() + 60000; return this._render(true);
      case "reboot":
        this._menu = null;
        return s && this._confirm({ title: t.confirmReboot(s.name), text: t.confirmRebootText, go: t.rebootGo, danger: false, run: () => this._press(s, "reboot", t.pendingReboot) });
      case "poweroff":
        this._menu = null;
        return s && this._confirm({ title: t.confirmOff(s.name), text: t.confirmOffText, go: t.offGo, danger: true, run: () => this._press(s, "poweroff", t.pendingPoweroff) });
      case "alert-open": this._menu = null; this._alert = { title: "", message: "" }; return this._render(true);
      case "alert-cancel": case "alert-bg": this._alert = null; return this._render(true);
      case "alert-end": return this._confirm({ title: t.confirmEnd, text: t.confirmEndText, go: t.endGo, danger: false, run: () => this._call("end_emergency", {}) });
      case "undo": { const u = this._toast?.undo; this._toast = null; this._render(true); return u && this._hass.callService("select", "select_option", { entity_id: u.eid, option: u.option }).catch((e) => this._fail(e)); }
      case "dlg-ok": { const run = this._dialog?.run; this._dialog = null; this._render(true); return run && run(); }
      case "dlg-cancel": case "dlg-bg": this._dialog = null; return this._render(true);
      default: return undefined;
    }
  }

  _confirm(d) { this._dialog = d; this._render(true); }

  _fail(err) {
    const message = this._t.failed(err?.message || String(err));
    this.dispatchEvent(new CustomEvent("hass-notification", { bubbles: true, composed: true, detail: { message } }));
  }

  async _call(service, data, target) {
    try { await this._hass.callService("linkivi", service, data, target); } catch (err) { this._fail(err); }
  }

  /** Changer la liste diffusée : un clic, publiée aussitôt ; une bulle « Annuler » pendant 10 s remet l'ancienne. */
  async _choose(s, option) {
    if (!option || option === s.plName) return;
    const before = s.plName;
    try {
      await this._hass.callService("select", "select_option", { entity_id: s.playlist, option });
      this._toast = { text: this._t.played(option, s.name), undo: before ? { eid: s.playlist, option: before } : null, until: Date.now() + UNDO_MS };
      this._render(true);
    } catch (err) { this._fail(err); }
  }

  _startAlert() {
    const root = this.shadowRoot;
    const title = (root.querySelector("#lk-at")?.value || "").trim();
    const message = (root.querySelector("#lk-am")?.value || "").trim();
    if (!title) { root.querySelector("#lk-at")?.focus(); return; }
    this._alert = null;
    this._render(true);
    // les écrans de la carte (filtre « screens »), sinon tous
    const target = (this._config.screens || []).length ? { device_id: this._items.map((x) => x.id) } : undefined;
    this._call("start_emergency", message ? { title, message } : { title }, target);
  }

  async _toggle(s, on) {
    this._optimistic[s.id] = { on, until: Date.now() + 8000 };
    this._render(true);
    try {
      await this._hass.callService("switch", on ? "turn_on" : "turn_off", { entity_id: s.sw });
    } catch (err) {
      delete this._optimistic[s.id];
      this._fail(err);
      this._render(true);
    }
  }

  async _press(s, role, label) {
    this._pending[s.id] = { label, until: Date.now() + PENDING_MS[role] };
    this._render(true);
    try {
      await this._hass.callService("button", "press", { entity_id: s[role] });
    } catch (err) {
      delete this._pending[s.id];
      this._fail(err);   // Linkivi dit pourquoi : écran hors ligne, commande déjà en cours, appareil non compatible…
      this._render(true);
    }
  }
}

/* ── éditeur visuel : l'éditeur de formulaire de Home Assistant (ha-form) ── */
class LinkivScreensCardEditor extends HTMLElement {
  setConfig(config) { this._config = config; this._draw(); }
  set hass(hass) { this._hass = hass; this._draw(); }

  _names() {
    const names = new Set();
    for (const reg of Object.values(this._hass?.entities || {})) {
      if (reg.platform === "linkivi" && reg.device_id && reg.translation_key !== "emergency") {
        const dev = this._hass.devices?.[reg.device_id];
        const n = dev?.name_by_user || dev?.name;
        if (n && dev?.model !== "Organisation") names.add(n);
      }
    }
    return [...names].sort((a, b) => a.localeCompare(b, "fr", { sensitivity: "base" }));
  }

  _draw() {
    if (!this._config || !this._hass) return;
    const lang = (this._hass.language || "en").startsWith("fr") ? "fr" : "en";
    const e = TEXTS[lang].ed;
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.addEventListener("value-changed", (ev) => {
        const config = { ...ev.detail.value };
        if (!config.screens?.length) delete config.screens;
        if (!config.title) delete config.title;
        if (!config.accent_color) delete config.accent_color;
        this.dispatchEvent(new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }));
      });
      this.appendChild(this._form);
    }
    this._form.hass = this._hass;
    this._form.data = { ...LinkivScreensCard.defaults(), ...this._config };
    this._form.computeLabel = (s) => e[s.name] || s.name;
    this._form.schema = [
      { name: "title", selector: { text: {} } },
      { name: "style", selector: { select: { mode: "box", options: [{ value: "list", label: e.list }, { value: "cards", label: e.cards }] } } },
      { name: "screens", selector: { select: { multiple: true, mode: "dropdown", options: this._names() } } },
      { name: "show_playlist", selector: { boolean: {} } },
      { name: "show_preview", selector: { boolean: {} } },
      { name: "preview_interval", selector: { number: { min: 1, max: 60, mode: "box", unit_of_measurement: "min" } } },
      { name: "show_player_restart", selector: { boolean: {} } },
      { name: "show_device_actions", selector: { boolean: {} } },
      { name: "show_group_buttons", selector: { boolean: {} } },
      { name: "hide_offline", selector: { boolean: {} } },
      { name: "show_emergency", selector: { boolean: {} } },
      { name: "emergency_for_all", selector: { boolean: {} } },
      { name: "accent_color", selector: { text: {} } },
    ];
  }
}

if (!customElements.get("linkivi-screens-card")) customElements.define("linkivi-screens-card", LinkivScreensCard);
if (!customElements.get("linkivi-screens-card-editor")) customElements.define("linkivi-screens-card-editor", LinkivScreensCardEditor);

window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === "linkivi-screens-card")) {
  window.customCards.push({
    type: "linkivi-screens-card",
    name: "Écrans Linkivi",
    description: "Voir et commander les écrans Linkivi : liste diffusée, aperçu du direct, écran, player, appareil, alerte d'urgence.",
    preview: false,
  });
}
console.info(`%c LINKIVI-SCREENS-CARD %c ${CARD_VERSION} `, "color:#fff;background:#0B1F3A", "color:#0B1F3A;background:#3B82C4");
