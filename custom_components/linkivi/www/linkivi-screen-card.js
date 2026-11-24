/*
 * Carte Home Assistant « Écran Linkivi » (linkivi-screen-card), version 3 (§351, maquette maquettes/ha-carte-ecran-et-musique.html).
 * Un écran par carte (remplace la carte « Écrans Linkivi » de plusieurs écrans) : état, aperçu du direct, liste diffusée, veille ou réveil,
 * redémarrage du player ; redémarrer et éteindre l'appareil dans le menu ⋮, avec confirmation ; diagnostic (processeur, disque, mémoire,
 * Wi-Fi, alimentation, batterie : « Inconnu » quand l'appareil ne les donne pas, orange et rouge au-delà des seuils) ; version, matériel, démarrage.
 * On choisit l'appareil ; les entités sont retrouvées par leur clé de traduction. Sans dépendance : élément natif + shadow DOM.
 * Servie par l'intégration (/linkivi/linkivi-screen-card.js) : chargée toute seule, ou déclarée en ressource « module JavaScript ».
 */
const CARD_VERSION = "3.0.0";

const TEXTS = {
  fr: {
    pick: "Choisissez un écran Linkivi dans les réglages de la carte.", gone: "Cet écran n'est plus dans Home Assistant.",
    states: { online: "En ligne", offline: "Hors ligne", updating: "Mise à jour", asleep: "En veille", paused: "En pause" },
    sleep: "Mettre en veille", wake: "Réveiller", restartPlayer: "Redémarrer le player",
    openLinkivi: "Ouvrir dans Linkivi", deviceInfo: "Fiche de l'appareil", reboot: "Redémarrer l'appareil…", powerOff: "Éteindre l'appareil…", confirmHint: "Une confirmation est demandée avant d'envoyer.",
    confirmReboot: (n) => `Redémarrer « ${n} » ?`, confirmRebootText: "L'appareil sera hors ligne quelques minutes, puis Linkivi reprend l'affichage.", rebootGo: "Redémarrer",
    confirmOff: (n) => `Éteindre « ${n} » ?`, confirmOffText: "Linkivi ne pourra pas le rallumer : il faudra appuyer sur son bouton ou remettre le courant.", offGo: "Éteindre",
    cancel: "Annuler", playlist: "Liste diffusée", noPlaylist: "Aucune liste",
    preview: "Aperçu du direct", refresh: "Actualiser", noPreview: "Pas d'aperçu du direct pour ce player",
    offline: "Hors ligne", lastContact: (d) => `dernier contact ${d}`, asleep: "Écran en veille",
    diag: "Diagnostic", cpu: "Processeur", disk: "Disque", mem: "Mémoire", wifi: "Wi-Fi", power: "Alimentation", battery: "Batterie",
    unknown: "Inconnu", free: (g) => `${g} Go libres`, powerOk: "Correcte", powerBad: "Insuffisante", charging: "en charge", notCharging: "pas en charge", weak: "faible",
    player: (v) => `Player ${v}`, booted: (d) => `Démarré ${d}`, now: "à l'instant", ago: (d) => `il y a ${d}`,
    minutes: (n) => `${n} min`, hours: (n) => `${n} h`, days: (n) => `${n} j`, failed: (m) => `Linkivi : ${m}`,
    ed: { device: "Écran", show_preview: "Aperçu du direct", show_commands: "Commandes", show_diagnostic: "Diagnostic", style: "Style", normal: "Normal", glass: "Verre" },
  },
  en: {
    pick: "Choose a Linkivi screen in the card settings.", gone: "This screen is no longer in Home Assistant.",
    states: { online: "Online", offline: "Offline", updating: "Updating", asleep: "Asleep", paused: "Paused" },
    sleep: "Put to sleep", wake: "Wake up", restartPlayer: "Restart player",
    openLinkivi: "Open in Linkivi", deviceInfo: "Device page", reboot: "Restart device…", powerOff: "Power off device…", confirmHint: "You will be asked to confirm.",
    confirmReboot: (n) => `Restart “${n}”?`, confirmRebootText: "The device will be offline for a few minutes, then Linkivi resumes the display.", rebootGo: "Restart",
    confirmOff: (n) => `Power off “${n}”?`, confirmOffText: "Linkivi cannot turn it back on: someone must press its button or restore power.", offGo: "Power off",
    cancel: "Cancel", playlist: "Playlist", noPlaylist: "No playlist",
    preview: "Live preview", refresh: "Refresh", noPreview: "No live preview for this player",
    offline: "Offline", lastContact: (d) => `last seen ${d}`, asleep: "Screen asleep",
    diag: "Diagnostics", cpu: "CPU", disk: "Disk", mem: "Memory", wifi: "Wi-Fi", power: "Power supply", battery: "Battery",
    unknown: "Unknown", free: (g) => `${g} GB free`, powerOk: "OK", powerBad: "Too low", charging: "charging", notCharging: "not charging", weak: "weak",
    player: (v) => `Player ${v}`, booted: (d) => `Started ${d}`, now: "just now", ago: (d) => `${d} ago`,
    minutes: (n) => `${n} min`, hours: (n) => `${n} h`, days: (n) => `${n} d`, failed: (m) => `Linkivi: ${m}`,
    ed: { device: "Screen", show_preview: "Live preview", show_commands: "Commands", show_diagnostic: "Diagnostics", style: "Style", normal: "Normal", glass: "Glass" },
  },
};

const ICON = {
  dots: '<svg viewBox="0 0 24 24" class="fill"><circle cx="12" cy="5" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="12" cy="19" r="1.6"/></svg>',
  moon: '<svg viewBox="0 0 24 24"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>',
  sun: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
  restart: '<svg viewBox="0 0 24 24"><path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><path d="M21 3v5h-5"/></svg>',
  chip: '<svg viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="2"/><path d="M9 9h6v6H9z"/></svg>',
  power: '<svg viewBox="0 0 24 24"><path d="M12 2v10"/><path d="M18.4 6.6a9 9 0 1 1-12.8 0"/></svg>',
  open: '<svg viewBox="0 0 24 24"><path d="M15 3h6v6M10 14 21 3M21 14v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5"/></svg>',
  info: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8v.01"/></svg>',
  list: '<svg viewBox="0 0 24 24"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></svg>',
  chevron: '<svg viewBox="0 0 24 24"><path d="m6 9 6 6 6-6"/></svg>',
  cam: '<svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="12" rx="2"/></svg>',
  cloud: '<svg viewBox="0 0 24 24"><path d="M2 2l20 20M8.5 16.5a5 5 0 0 1 7 0M5 13a10 10 0 0 1 5.2-2.8M19 13a10 10 0 0 0-2.3-1.6M2 8.8a15 15 0 0 1 4.6-2.9M22 8.8A15 15 0 0 0 11 5M12 20h.01"/></svg>',
  temp: '<svg viewBox="0 0 24 24"><path d="M14 14.8V4a2 2 0 0 0-4 0v10.8a4 4 0 1 0 4 0z"/></svg>',
  disk: '<svg viewBox="0 0 24 24"><ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/></svg>',
  mem: '<svg viewBox="0 0 24 24"><rect x="4" y="7" width="16" height="10" rx="1"/><path d="M8 7V4M12 7V4M16 7V4M8 20v-3M12 20v-3M16 20v-3"/></svg>',
  wifi: '<svg viewBox="0 0 24 24"><path d="M5 12.6a10 10 0 0 1 14 0M8.5 16a5 5 0 0 1 7 0M2 9a15 15 0 0 1 20 0M12 20h.01"/></svg>',
  bolt: '<svg viewBox="0 0 24 24"><path d="M13 2 3 14h9l-1 8 10-12h-9z"/></svg>',
  battery: '<svg viewBox="0 0 24 24"><rect x="2" y="7" width="18" height="10" rx="2"/><path d="M22 11v2"/></svg>',
};

// Rôle des entités d'un écran, d'après leur clé de traduction (batterie et charge : d'après leur classe)
const ROLE_BY_KEY = {
  online: "online", screen: "sw", restart_player: "player", reboot: "reboot", power_off: "poweroff", screen_off: "sleep", wake: "wake",
  playlist: "playlist", state: "state", last_seen: "seen", preview: "cam", booted_at: "boot", player_version: "version",
  cpu_temperature: "cpu", disk_used: "disk", memory_used: "mem", wifi_signal: "wifi", under_voltage: "uv",
};
// Seuils d'alerte (décision 3) : orange puis rouge
const LIMITS = { cpu: [70, 80], disk: [80, 90], mem: [85, 95] };
const PENDING_MS = { player: 20000, reboot: 120000, poweroff: 60000, sleep: 15000, wake: 15000 };

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const num = (st) => (st && !["unknown", "unavailable", ""].includes(st.state) && !isNaN(parseFloat(st.state)) ? parseFloat(st.state) : null);
const fmt = (v, d, lang) => v.toLocaleString(lang, { maximumFractionDigits: d, minimumFractionDigits: 0 });

const CSS = `:host{display:block;--lk:#2a86ee;--lk-ok:var(--success-color,#43a047);--lk-warn:var(--warning-color,#ffa726);--lk-off:var(--disabled-color,#9e9e9e);
  --lk-chip:var(--secondary-background-color,rgba(127,127,127,.15));--lk-text:var(--primary-text-color);--lk-sec:var(--secondary-text-color);
  --lk-div:var(--divider-color,rgba(127,127,127,.3));--lk-danger:var(--error-color,#d32f2f);--lk-card:var(--ha-card-background,var(--card-background-color,#fff))}
ha-card{overflow:hidden;position:relative;color:var(--lk-text)}
ha-card.glass{background:radial-gradient(120% 90% at 0% 0%,color-mix(in srgb,var(--lk) 26%,transparent),transparent 60%),var(--lk-card)}
svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;flex:none}svg.fill{fill:currentColor;stroke:none}
button{font:inherit;color:inherit;cursor:pointer}
.hd{display:flex;align-items:center;gap:12px;padding:14px 14px 10px 16px}
.hd .tt{flex:1;min-width:0}.hd .n{font-size:18px;font-weight:500;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.hd .d{font-size:12.5px;color:var(--lk-sec);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pill{display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:500;padding:4px 10px 4px 8px;border-radius:14px;background:color-mix(in srgb,var(--c) 15%,transparent);color:var(--c);flex:none}
.pill:before{content:"";width:8px;height:8px;border-radius:50%;background:var(--c)}
.pill.online{--c:var(--lk-ok)}.pill.asleep,.pill.paused{--c:var(--lk)}.pill.offline{--c:var(--lk-off)}.pill.updating{--c:var(--lk-warn)}
.ib{width:34px;height:34px;border:0;border-radius:50%;background:color-mix(in srgb,var(--lk-text) 8%,transparent);display:inline-flex;align-items:center;justify-content:center;padding:0;flex:none}
.pv{margin:0 14px;border-radius:10px;overflow:hidden;position:relative;aspect-ratio:16/9;background:#0B1F3A}
.pv img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.pv .cap{position:absolute;left:0;right:0;bottom:0;padding:22px 10px 8px;display:flex;align-items:center;gap:6px;background:linear-gradient(transparent,rgba(0,0,0,.65));color:#fff;font-size:12px}
.pv .cap svg{width:14px;height:14px}
.pv .rf{position:absolute;top:8px;right:8px;width:30px;height:30px;border-radius:50%;background:rgba(0,0,0,.45);color:#fff;display:grid;place-items:center;border:0;padding:0}
.pv .rf svg{width:16px;height:16px}
.pv .msg{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;color:#fff;font-size:13px;text-align:center;padding:0 16px}
.pv .msg b{font-weight:500;font-size:14px}.pv .msg small{opacity:.7;font-size:12px}.pv .msg svg{width:26px;height:26px}
.pv.out{background:repeating-linear-gradient(135deg,#23272e 0 14px,#1c2026 14px 28px)}
.pv.sleep{background:#05080d}.pv.sleep .msg{color:#8fb3e0;flex-direction:row}.pv.sleep .msg svg{width:18px;height:18px}
.pv.none{background:color-mix(in srgb,var(--lk-text) 6%,transparent)}.pv.none .msg{color:var(--lk-sec)}
.ls{margin:12px 14px 0;display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:10px;background:var(--lk-chip);font-size:13.5px;border:0;width:calc(100% - 28px);text-align:left}
.ls .l{flex:1;min-width:0}.ls .l small{display:block;font-size:11px;color:var(--lk-sec);line-height:1.1}.ls .l b{font-weight:500;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ls:disabled{cursor:default;opacity:.7}
.ac{display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:12px 14px 4px}
.ac button{border:0;background:var(--lk-chip);border-radius:12px;padding:10px 12px;display:flex;align-items:center;justify-content:center;gap:8px;font-weight:500;font-size:13px}
.ac button.on{background:color-mix(in srgb,var(--lk) 18%,transparent);color:var(--lk)}
.ac button:disabled{opacity:.38;cursor:default}
.dg{margin:10px 14px 0;border-top:1px solid var(--lk-div);padding-top:10px}
.dg .h{font-size:12px;font-weight:500;color:var(--lk-sec);text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px}
.gr{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.m{border-radius:10px;padding:8px 10px;background:color-mix(in srgb,var(--lk-text) 4%,transparent);display:flex;flex-direction:column;gap:4px;min-width:0}
.m .k{display:flex;align-items:center;gap:6px;font-size:11.5px;color:var(--lk-sec);white-space:nowrap;overflow:hidden}.m .k svg{width:14px;height:14px}
.m .v{font-size:16px;font-weight:500;line-height:1.15}.m .v small{font-size:11.5px;font-weight:400;color:var(--lk-sec);margin-left:3px}
.m .bar{height:4px;border-radius:2px;background:var(--lk-div);overflow:hidden}.m .bar i{display:block;height:100%;background:var(--c,var(--lk-ok))}
.m.warn{--c:var(--lk-warn)}.m.warn .v{color:var(--lk-warn)}
.m.bad{--c:var(--lk-danger);background:color-mix(in srgb,var(--lk-danger) 10%,transparent)}.m.bad .v{color:var(--lk-danger)}
.m.na .v{color:var(--lk-sec);font-weight:400;font-size:14px}
.wf{display:inline-flex;align-items:flex-end;gap:2px;height:13px;margin-left:6px;vertical-align:-1px}.wf i{width:3px;border-radius:1px;background:var(--c,var(--lk-ok))}.wf i.x{background:var(--lk-div)}
.ft{padding:10px 16px 14px;font-size:12px;color:var(--lk-sec);display:flex;flex-direction:column;gap:2px}.ft b{font-weight:500;color:var(--lk-text)}
.empty{padding:16px 18px;color:var(--lk-sec)}
.pend{margin:8px 14px 0;font-size:12.5px;color:var(--lk-warn)}
.pop{position:absolute;right:14px;top:52px;z-index:5;min-width:230px;background:var(--lk-card);border:1px solid var(--lk-div);border-radius:10px;box-shadow:0 6px 22px rgba(0,0,0,.25);padding:4px;font-size:13.5px}
.pop button{display:flex;width:100%;gap:10px;align-items:center;border:0;background:none;border-radius:6px;padding:9px 12px;text-align:left}
.pop button:hover{background:var(--lk-chip)}.pop .red{color:var(--lk-danger)}.pop hr{border:0;border-top:1px solid var(--lk-div);margin:4px 0}
.pop .hint{display:block;font-size:11.5px;color:var(--lk-sec);padding:2px 12px 6px}
.pop.pl{left:14px;right:14px;top:auto;max-height:260px;overflow:auto}.pop.pl button.cur{font-weight:500;color:var(--lk)}
.ov{position:absolute;inset:0;z-index:9;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;padding:16px}
.dlg{background:var(--lk-card);border-radius:14px;padding:18px 18px 12px;max-width:340px;box-shadow:0 10px 30px rgba(0,0,0,.35)}
.dlg .t{font-size:17px;font-weight:500;margin-bottom:6px}.dlg p{margin:0 0 14px;color:var(--lk-sec);font-size:13.5px;line-height:1.45}
.dlg .f{display:flex;justify-content:flex-end;gap:8px}.dlg .f button{border:0;background:none;padding:8px 12px;border-radius:8px;font-weight:500;color:var(--lk)}
.dlg .f .go{background:var(--lk);color:#fff}.dlg .f .go.red{background:var(--lk-danger)}`;

class LinkivScreenCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._menu = null;      // « dev » : menu ⋮ ; « pl » : choix de la liste
    this._dialog = null;    // confirmation : { title, text, go, red, role }
    this._pending = null;   // { role, until }
    this._shot = 0;         // nouvelle image de l'aperçu demandée à la main
    this._sig = "";
    this.shadowRoot.addEventListener("click", (e) => this._click(e));
    this._onDoc = (e) => { if (this._menu && !e.composedPath().some((el) => el.classList?.contains("pop") || el.dataset?.act === "menu" || el.dataset?.act === "pl")) { this._menu = null; this._render(true); } };
  }

  static getConfigElement() { return document.createElement("linkivi-screen-card-editor"); }
  static getStubConfig(hass) {
    const reg = Object.values(hass?.entities || {}).find((r) => r.platform === "linkivi" && r.translation_key === "online");
    return { type: "custom:linkivi-screen-card", device: reg?.device_id || "" };
  }
  static defaults() { return { show_preview: true, show_commands: true, show_diagnostic: true, style: "normal" }; }

  setConfig(config) { this._config = { ...LinkivScreenCard.defaults(), ...(config || {}) }; this._render(true); }
  set hass(hass) { this._hass = hass; this._render(false); }
  getCardSize() { return 8; }
  connectedCallback() { document.addEventListener("click", this._onDoc); this._tmr = setInterval(() => this._render(true), 30000); }
  disconnectedCallback() { document.removeEventListener("click", this._onDoc); clearInterval(this._tmr); }

  get _lang() { return (this._hass?.language || "en").startsWith("fr") ? "fr" : "en"; }
  get _t() { return TEXTS[this._lang]; }

  /* entités de l'appareil choisi, par rôle */
  _entities() {
    const id = this._config.device, out = {};
    if (!id || !this._hass) return out;
    for (const [eid, reg] of Object.entries(this._hass.entities || {})) {
      if (reg.device_id !== id || reg.platform !== "linkivi") continue;
      let role = ROLE_BY_KEY[reg.translation_key];
      if (!role) {
        const dc = this._hass.states[eid]?.attributes?.device_class;
        role = eid.startsWith("sensor.") && dc === "battery" ? "battery" : eid.startsWith("binary_sensor.") && dc === "battery_charging" ? "charging" : null;
      }
      if (role) out[role] = eid;
    }
    return out;
  }

  _since(iso) {
    const t = this._t, ms = Date.now() - new Date(iso).getTime();
    if (!(ms >= 0)) return "";
    const m = Math.round(ms / 60000);
    return m < 1 ? t.now : t.ago(m < 60 ? t.minutes(m) : m < 2880 ? t.hours(Math.round(m / 60)) : t.days(Math.round(m / 1440)));
  }

  /* une tuile du diagnostic ; v = null → « Inconnu » */
  _tile(icon, label, v, sub, level, pct, extra) {
    if (v == null) return `<div class="m na"><div class="k">${ICON[icon]}${esc(label)}</div><div class="v">${esc(this._t.unknown)}</div></div>`;
    return `<div class="m ${level || ""}"><div class="k">${ICON[icon]}${esc(label)}</div><div class="v">${v}${sub ? `<small>${sub}</small>` : ""}${extra || ""}</div>${pct != null ? `<div class="bar"><i style="width:${Math.max(0, Math.min(100, pct))}%"></i></div>` : ""}</div>`;
  }
  _lvl(v, [w, b]) { return v >= b ? "bad" : v >= w ? "warn" : ""; }

  _diag(e) {
    const t = this._t, h = this._hass, L = this._lang;
    const cpu = num(h.states[e.cpu]), disk = num(h.states[e.disk]), mem = num(h.states[e.mem]), wifi = num(h.states[e.wifi]), bat = num(h.states[e.battery]);
    const da = h.states[e.disk]?.attributes || {}, uv = h.states[e.uv]?.state, ch = h.states[e.charging]?.state;
    const wl = wifi == null ? "" : wifi <= -80 ? "bad" : wifi <= -70 ? "warn" : "";
    const bars = wifi == null ? "" : `<span class="wf">${[30, 55, 80, 100].map((x, i) => `<i${i < (wifi > -60 ? 4 : wifi > -70 ? 3 : wifi > -80 ? 2 : 1) ? "" : ' class="x"'} style="height:${x}%"></i>`).join("")}</span>`;
    return `<div class="dg"><div class="h">${esc(t.diag)}</div><div class="gr">
      ${this._tile("temp", t.cpu, cpu == null ? null : fmt(cpu, 1, L), "°C", cpu == null ? "" : this._lvl(cpu, LIMITS.cpu), cpu)}
      ${this._tile("disk", t.disk, disk == null ? null : fmt(disk, 0, L), "%" + (da.free_gb != null ? " · " + esc(t.free(fmt(da.free_gb, 1, L))) : ""), disk == null ? "" : this._lvl(disk, LIMITS.disk), disk)}
      ${this._tile("mem", t.mem, mem == null ? null : fmt(mem, 0, L), "%", mem == null ? "" : this._lvl(mem, LIMITS.mem), mem)}
      ${this._tile("wifi", t.wifi, wifi == null ? null : String(wifi).replace("-", "−"), "dBm" + (wl === "bad" ? " · " + esc(t.weak) : ""), wl, null, bars)}
      ${this._tile("bolt", t.power, uv === "on" ? esc(t.powerBad) : uv === "off" ? esc(t.powerOk) : null, "", uv === "on" ? "bad" : "")}
      ${this._tile("battery", t.battery, bat == null ? null : fmt(bat, 0, L), "%" + (ch === "on" ? " · " + esc(t.charging) : ch === "off" ? " · " + esc(t.notCharging) : ""), bat == null ? "" : bat <= 10 ? "bad" : bat <= 20 ? "warn" : "", bat)}
    </div></div>`;
  }

  _render(force) {
    if (!this._hass) return;
    const t = this._t, h = this._hass, c = this._config, e = this._entities();
    const watch = Object.values(e).map((x) => { const s = h.states[x]; return s ? s.state + "|" + (s.attributes.entity_picture || "") + "|" + (s.attributes.options || []).length : ""; });
    const sig = JSON.stringify([c, watch, this._menu, this._dialog, this._pending, this._shot, h.language]);
    if (!force && sig === this._sig) return;
    this._sig = sig;
    let body;
    if (!c.device) body = `<div class="empty">${esc(t.pick)}</div>`;
    else if (!e.online && !e.state) body = `<div class="empty">${esc(t.gone)}</div>`;
    else body = this._screen(e);
    this.shadowRoot.innerHTML = `<style>${CSS}</style><ha-card class="${c.style === "glass" ? "glass" : ""}">${body}</ha-card>`;
  }

  _screen(e) {
    const t = this._t, h = this._hass, c = this._config;
    const dev = h.devices?.[c.device] || {};
    const name = dev.name_by_user || dev.name || "Écran";
    const area = h.areas?.[dev.area_id]?.name || "";
    const model = (dev.model || "").replace(/^Player /, "");
    const online = h.states[e.online]?.state === "on";
    let status = h.states[e.state]?.state;
    if (!t.states[status]) status = online ? "online" : "offline";
    const asleep = status === "asleep";
    const pend = this._pending && this._pending.until > Date.now() ? this._pending.role : null;
    // aperçu
    let pv = "";
    if (c.show_preview) {
      if (!online) {
        const seen = h.states[e.seen]?.state;
        pv = `<div class="pv out"><div class="msg">${ICON.cloud}<b>${esc(t.offline)}</b>${seen && seen !== "unknown" && seen !== "unavailable" ? `<small>${esc(t.lastContact(this._since(seen)))}</small>` : ""}</div></div>`;
      } else if (asleep) pv = `<div class="pv sleep"><div class="msg">${ICON.moon}${esc(t.asleep)}</div></div>`;
      else {
        const pic = h.states[e.cam]?.attributes?.entity_picture;
        pv = pic
          ? `<div class="pv"><img alt="" src="${esc(pic + (pic.includes("?") ? "&" : "?") + "lk=" + Math.floor(Date.now() / 60000) + "-" + this._shot)}"><button class="rf" data-act="shot" title="${esc(t.refresh)}">${ICON.restart}</button><div class="cap">${ICON.cam}${esc(t.preview)}</div></div>`
          : `<div class="pv none"><div class="msg">${esc(t.noPreview)}</div></div>`;
      }
    }
    // liste diffusée
    const pl = h.states[e.playlist];
    const plName = pl && !["unknown", "unavailable"].includes(pl.state) ? pl.state : "";
    const ls = e.playlist ? `<button class="ls" data-act="pl" ${pl?.attributes?.options?.length ? "" : "disabled"}>${ICON.list}<span class="l"><small>${esc(t.playlist)}</small><b>${esc(plName || t.noPlaylist)}</b></span>${ICON.chevron}</button>
      ${this._menu === "pl" ? `<div class="pop pl">${(pl.attributes.options || []).map((o) => `<button data-act="pick" data-v="${esc(o)}" class="${o === plName ? "cur" : ""}">${esc(o)}</button>`).join("")}</div>` : ""}` : "";
    // commandes : veille ou réveil, redémarrer le player
    const sleepRole = asleep ? (e.wake ? "wake" : e.sw ? "swon" : null) : (e.sleep ? "sleep" : e.sw ? "swoff" : null);
    const ac = c.show_commands ? `<div class="ac">
      <button data-act="cmd" data-v="${sleepRole || ""}" class="${asleep ? "on" : ""}" ${sleepRole && !pend ? "" : "disabled"}>${asleep ? ICON.sun + esc(t.wake) : ICON.moon + esc(t.sleep)}</button>
      <button data-act="cmd" data-v="player" ${e.player && online && !pend ? "" : "disabled"}>${ICON.restart}${esc(t.restartPlayer)}</button></div>` : "";
    // menu ⋮
    const cfg = dev.configuration_url;
    const menu = this._menu === "dev" ? `<div class="pop">
      ${cfg ? `<button data-act="open">${ICON.open}${esc(t.openLinkivi)}</button>` : ""}
      <button data-act="device">${ICON.info}${esc(t.deviceInfo)}</button>
      ${e.reboot || e.poweroff ? "<hr>" : ""}
      ${e.reboot ? `<button data-act="ask" data-v="reboot">${ICON.chip}${esc(t.reboot)}</button>` : ""}
      ${e.poweroff ? `<button data-act="ask" data-v="poweroff" class="red">${ICON.power}${esc(t.powerOff)}</button>` : ""}
      ${e.reboot || e.poweroff ? `<span class="hint">${esc(t.confirmHint)}</span>` : ""}</div>` : "";
    // pied : version, matériel, démarrage
    const ver = h.states[e.version], va = ver?.attributes || {};
    const hw = [va.model, va.os].filter(Boolean).join(" · ");
    const boot = h.states[e.boot]?.state;
    const ft = `<div class="ft">${ver && !["unknown", "unavailable"].includes(ver.state) ? `<span><b>${esc(t.player(ver.state))}</b>${hw ? " · " + esc(hw) : ""}</span>` : hw ? `<span>${esc(hw)}</span>` : ""}
      ${boot && !["unknown", "unavailable"].includes(boot) ? `<span>${esc(t.booted(this._since(boot)))}</span>` : ""}</div>`;
    const dlg = this._dialog ? `<div class="ov" data-act="dlg-bg"><div class="dlg" role="dialog"><div class="t">${esc(this._dialog.title)}</div><p>${esc(this._dialog.text)}</p>
      <div class="f"><button data-act="dlg-no">${esc(t.cancel)}</button><button class="go ${this._dialog.red ? "red" : ""}" data-act="dlg-ok">${esc(this._dialog.go)}</button></div></div></div>` : "";
    return `<div class="hd"><div class="tt"><div class="n">${esc(name)}</div><div class="d">${esc([area, model].filter(Boolean).join(" · "))}</div></div>
      <span class="pill ${status}">${esc(t.states[status])}</span><button class="ib" data-act="menu" title="⋮">${ICON.dots}</button></div>
      ${menu}${pv}${ls}${ac}${c.show_diagnostic ? this._diag(e) : ""}${ft}${dlg}`;
  }

  _click(ev) {
    const el = ev.composedPath().find((x) => x.dataset?.act);
    if (!el || el.disabled) return;
    const act = el.dataset.act, v = el.dataset.v, t = this._t, e = this._entities();
    const dev = this._hass.devices?.[this._config.device] || {};
    const name = dev.name_by_user || dev.name || "";
    if (act === "dlg-bg" && ev.target !== el) return;
    ev.stopPropagation();
    switch (act) {
      case "menu": this._menu = this._menu === "dev" ? null : "dev"; break;
      case "pl": this._menu = this._menu === "pl" ? null : "pl"; break;
      case "pick": this._menu = null; this._call("select", "select_option", { entity_id: e.playlist, option: v }); break;
      case "shot": this._shot++; break;
      case "open": this._menu = null; window.open(dev.configuration_url, "_blank", "noopener"); break;
      case "device":
        this._menu = null;
        history.pushState(null, "", `/config/devices/device/${this._config.device}`);
        window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: false } }));
        break;
      case "ask":
        this._menu = null;
        this._dialog = v === "reboot"
          ? { role: "reboot", title: t.confirmReboot(name), text: t.confirmRebootText, go: t.rebootGo, red: false }
          : { role: "poweroff", title: t.confirmOff(name), text: t.confirmOffText, go: t.offGo, red: true };
        break;
      case "dlg-ok": { const r = this._dialog?.role; this._dialog = null; if (r) this._press(e[r], r); break; }
      case "dlg-no": case "dlg-bg": this._dialog = null; break;
      case "cmd":
        if (v === "swon" || v === "swoff") { this._call("switch", v === "swon" ? "turn_on" : "turn_off", { entity_id: e.sw }); this._pend(v === "swon" ? "wake" : "sleep"); }
        else if (v) this._press(e[v], v);
        break;
      default: return;
    }
    this._render(true);
  }

  _pend(role) { this._pending = { role, until: Date.now() + (PENDING_MS[role] || 15000) }; setTimeout(() => this._render(true), (PENDING_MS[role] || 15000) + 50); }
  _press(eid, role) { if (!eid) return; this._pend(role); this._call("button", "press", { entity_id: eid }); }
  async _call(domain, service, data) {
    try { await this._hass.callService(domain, service, data); }
    catch (err) {
      this._pending = null; this._render(true);
      this.dispatchEvent(new CustomEvent("hass-notification", { detail: { message: this._t.failed(err?.message || err) }, bubbles: true, composed: true }));
    }
  }
}

/* ── éditeur visuel : ha-form de Home Assistant ── */
class LinkivScreenCardEditor extends HTMLElement {
  setConfig(config) { this._config = config; this._draw(); }
  set hass(hass) { this._hass = hass; this._draw(); }
  _draw() {
    if (!this._config || !this._hass) return;
    const e = TEXTS[(this._hass.language || "en").startsWith("fr") ? "fr" : "en"].ed;
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.addEventListener("value-changed", (ev) => this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: { ...ev.detail.value } }, bubbles: true, composed: true })));
      this.appendChild(this._form);
    }
    this._form.hass = this._hass;
    this._form.data = { ...LinkivScreenCard.defaults(), ...this._config };
    this._form.computeLabel = (s) => e[s.name] || s.name;
    this._form.schema = [
      { name: "device", required: true, selector: { device: { integration: "linkivi" } } },
      { name: "show_preview", selector: { boolean: {} } },
      { name: "show_commands", selector: { boolean: {} } },
      { name: "show_diagnostic", selector: { boolean: {} } },
      { name: "style", selector: { select: { mode: "box", options: [{ value: "normal", label: e.normal }, { value: "glass", label: e.glass }] } } },
    ];
  }
}

if (!customElements.get("linkivi-screen-card")) customElements.define("linkivi-screen-card", LinkivScreenCard);
if (!customElements.get("linkivi-screen-card-editor")) customElements.define("linkivi-screen-card-editor", LinkivScreenCardEditor);

window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === "linkivi-screen-card")) {
  window.customCards.push({
    type: "linkivi-screen-card",
    name: "Écran Linkivi",
    description: "Un écran Linkivi : état, aperçu du direct, liste diffusée, veille et réveil, redémarrages, diagnostic de l'appareil.",
    preview: true,
  });
}
console.info(`%c LINKIVI-SCREEN-CARD %c ${CARD_VERSION} `, "color:#fff;background:#0B1F3A", "color:#0B1F3A;background:#3B82C4");
