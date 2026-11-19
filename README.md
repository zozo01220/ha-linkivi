# Linkivi pour Home Assistant

[![Version](https://img.shields.io/badge/version-1.9.0-2a86ee)](https://github.com/zozo01220/ha-linkivi/releases) [![HACS](https://img.shields.io/badge/HACS-d%C3%A9p%C3%B4t%20personnalis%C3%A9-41bdf5)](https://hacs.xyz/) ![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.11%2B-03a9f4)

Voir et commander ses écrans Linkivi depuis Home Assistant : allumer ou éteindre l'écran, redémarrer le player ou l'appareil, changer la liste diffusée, voir l'aperçu du direct, **y afficher un message** (sonnette, lave-linge terminé…) et déclencher l'**alerte d'urgence**. Une carte « Écrans Linkivi » est fournie pour le tableau de bord. **Huit blueprints prêts à l'emploi** (sonnette, fin de cycle, fuite → urgence, présence, chien de garde, batterie, Tempo, invités), avec leurs automatisations équivalentes : voir [AUTOMATISATIONS.md](AUTOMATISATIONS.md).

Chaque écran devient un **appareil** Home Assistant. À ne pas confondre avec l'intégration Home Assistant **de** Linkivi (lire et commander les appareils d'une maison sur les écrans) : ici, c'est l'inverse. Les deux se complètent (voir « Montrer les appareils de la maison sur les écrans »).

**Prérequis** : Home Assistant 2024.11 ou plus récent. **Tous les plans** de Linkivi, sans exception, et sans installer « Alerte d'urgence » dans le Store de Linkivi.

## Installer

1. **Par HACS** (conseillé) : HACS › menu ⋮ › **Dépôts personnalisés** › `https://github.com/zozo01220/ha-linkivi`, catégorie **Intégration** › Télécharger, puis redémarrez Home Assistant.
   **À la main** : copiez le dossier `custom_components/linkivi` dans `config/custom_components/` de Home Assistant, puis redémarrez Home Assistant.
2. Paramètres › Appareils et services › Ajouter une intégration › **Linkivi** › **Se connecter avec un code** : adresse de votre Linkivi (par exemple `https://linkivi.duckdns.org`).
3. Home Assistant affiche un **lien** et un **code** (8 lettres, `WDJB-MJHT`), valable 10 minutes. Ouvrez le lien : Linkivi s'ouvre (connectez-vous si besoin), vérifiez que le code est le même, choisissez l'organisation si vous en gérez plusieurs, puis **Autoriser**.
4. Home Assistant reçoit sa clé tout seul : les écrans apparaissent en quelques secondes. Ceux ajoutés plus tard dans Linkivi apparaissent seuls, **en direct**.

Qui peut autoriser : un administrateur de l'organisation, ou un membre qui publie **sans approbation**. Home Assistant agit ensuite au nom de cette personne, sans approbation. L'accès se retire dans Linkivi, Applications › Home Assistant › « Accès de Home Assistant » ; supprimer l'intégration dans Home Assistant le retire aussi.

**Avancé** : « Coller une clé d'API » marche toujours avec une clé du modèle « Home Assistant » créée dans « API et webhooks » (plan Pro).

## Mettre à jour

Par HACS : la mise à jour apparaît dans HACS (et dans Paramètres › Mises à jour). Installez-la, **redémarrez Home Assistant**, puis rechargez la page avec Ctrl+F5 pour la carte.

Depuis la 1.8.1, tant que Home Assistant n'a pas redémarré après une mise à jour, une **réparation « Linkivi : redémarrer Home Assistant »** apparaît dans Paramètres (vérifiée au démarrage puis toutes les 5 minutes) ; son bouton **Envoyer** redémarre Home Assistant. Sans redémarrage, Home Assistant continue de faire tourner l'ancienne version, même si les nouveaux fichiers sont installés.

**Reconfigurer** (nouvelle autorisation sans rien supprimer) : Paramètres › Appareils et services › **Linkivi** › menu **⋮** de l'organisation › **Reconfigurer** › « Se connecter avec un code », puis « Autoriser » dans Linkivi. La nouvelle clé reçoit tous les accès actuels du modèle « Home Assistant ». Les entités, les automatisations et le partage sont gardés. L'ancienne clé reste listée dans Linkivi (Applications › Home Assistant) : retirez-la si vous voulez.

À faire une fois si votre intégration a été reliée **avant la 1.7.1** : l'autorisation n'a peut-être pas l'urgence (ni la liste diffusée si elle date d'avant la 1.5), et l'action `linkivi.start_emergency` le signale. Reconfigurez comme ci-dessus.

Si Linkivi retire l'accès (clé révoquée ou expirée), Home Assistant demande de lui-même une **nouvelle authentification** sur la carte Linkivi : même parcours, par code ou en collant une clé.

## Ce que chaque écran offre

| Entité | Type | Rôle |
|---|---|---|
| **En ligne** | capteur binaire | L'écran a donné de ses nouvelles ces 90 dernières secondes. Attributs : état, dernier contact, aire, zone, liste, résolution. |
| **Écran** | interrupteur | Allumé = éveillé. Éteindre = veille manuelle jusqu'au réveil. Allumer = réveil d'**une heure**, puis les plages de veille et les calendriers reprennent la main (comme « Réveiller » dans Linkivi). Marche aussi quand l'écran est hors ligne : la consigne est lue à son retour. |
| **Redémarrer le player** | bouton | Relance l'application d'affichage. |
| **Redémarrer l'appareil** | bouton | Redémarre le PC, le Raspberry Pi ou l'appareil Android. |
| **Éteindre l'appareil** | bouton | Éteint l'appareil. **Linkivi ne peut pas le rallumer** : il faut le bouton ou le courant. |
| **Liste diffusée** | liste de choix | La liste de lecture de l'écran. En choisir une autre la publie aussitôt, sans approbation. Pas pour un écran de mur ni une borne. |
| **État** | capteur | En ligne, hors ligne, mise à jour, en veille ou en pause. |
| **Dernière connexion** | capteur (désactivé par défaut) | Dernier contact de l'écran. |
| **Aperçu du direct** | caméra | Ce que l'écran affiche (players Android et Raspberry Pi). Une nouvelle image est demandée au plus toutes les 60 s quand on la regarde. Un écran portrait peut arriver couché. |
| **Message** | notification | Pour l'action `notify.send_message` : une carte en coin (bas droite, 15 s), la diffusion continue. |
| **Batterie** et **En charge** | capteur, capteur binaire | Smartphones et tablettes Android seulement : niveau et branché ou non. |


Et pour l'organisation (appareil « Organisation ») :

| Entité | Type | Rôle |
|---|---|---|
| **Urgence en cours** | capteur binaire | Une alerte d'urgence est en cours sur au moins un écran. |
| **Tous les écrans** | notification | `notify.send_message` sur tous les écrans en ligne et éveillés. |

Un bouton n'existe que si le matériel sait faire la commande :

| Appareil | Player | Écran | Redémarrer | Éteindre |
|---|---|---|---|---|
| Windows, Raspberry Pi | oui | oui | oui | oui |
| Android, Android TV | oui | oui | seulement si l'app est propriétaire de l'appareil (`dpm set-device-owner`) | jamais |
| Navigateur | oui | oui | non | non |

Un écran de **mur** se commande en entier : un ordre sur un écran du mur part sur tous.

## Actions

Dans l'éditeur d'automatisations (Ajouter une action › Linkivi) ou dans Outils de développement › Actions :

| Action | Rôle |
|---|---|
| `linkivi.show_message` | Affiche un message par-dessus la diffusion (voir « Afficher un message sur un écran »). |
| `linkivi.clear_display` | Retire le message tout de suite. |
| `linkivi.show_list` | Diffuse une autre liste (`playlist` : nom de la liste). |
| `linkivi.start_emergency` | Déclenche l'alerte d'urgence (`title` 40 caractères, `message` 300) ; sans cible, sur tous les écrans. |
| `linkivi.end_emergency` | Lève toutes les alertes en cours. |

## Montrer les appareils de la maison sur les écrans

Dans Linkivi, Applications › Home Assistant › « Par l'intégration Linkivi » (conseillé). Puis, dans Home Assistant : Paramètres › Appareils et services › Linkivi › **Configurer** › « Partager avec Linkivi » : des pièces, des libellés ou des entités, et « Permettre aux écrans de commander ces appareils » (non par défaut). Les serrures et les alarmes ne se partagent qu'une à une. Linkivi ne garde alors **aucun jeton** de votre Home Assistant et n'a plus besoin du relais : il demande les états, l'historique et les images des caméras à l'intégration, qui ne répond que pour ce qui est partagé.

Déjà relié en direct ou par le relais ? Le bandeau « Passer par l'intégration » de Applications › Home Assistant fait la bascule dès que toutes les entités utilisées par vos écrans sont partagées ; l'ancien jeton est alors oublié.

### La musique en cours sur les écrans

Partagez un lecteur multimédia (enceinte, Spotify, Music Assistant, groupe Sonos…) comme n'importe quelle entité, par sa pièce, un libellé ou un à un. Dans Linkivi, ajoutez à une liste de lecture le contenu **« En cours de lecture »** et choisissez ce lecteur : pendant la lecture, l'écran montre la pochette, le titre, l'artiste et la progression, puis la liste reprend à l'arrêt. Trois façons de l'afficher : prendre tout l'écran, seulement à son tour dans la liste, ou en carte dans un coin. La pochette passe par l'intégration (1.9.0 ou plus) quand Home Assistant la sert lui-même.

## Temps réel et déclencheurs

L'intégration garde une connexion ouverte vers Linkivi : un écran mis en veille, changé de liste ou tombé apparaît dans Home Assistant **dans les secondes qui suivent**, sans relevé. La connexion part de Home Assistant (port 443 sortant) : rien à ouvrir chez vous. Si un proxy bloque les WebSockets, elle passe toute seule en HTTPS simple (attente longue). Après une coupure, elle reprend là où elle s'était arrêtée.

Chaque écran propose quatre **déclencheurs** dans l'éditeur d'automatisations (Déclencheur › Appareil › l'écran) :

| Déclencheur | Quand |
|---|---|
| ne répond plus | L'écran est hors ligne depuis le délai d'alerte des Réglages de Linkivi (hors veille). |
| est de retour | L'écran signalé hors ligne répond de nouveau. |
| affiche une nouvelle version | Une publication est arrivée sur l'écran. |
| affiche l'alerte d'urgence | L'écran confirme afficher une alerte d'urgence. |

Tous les événements de Linkivi passent aussi sur le bus de Home Assistant sous le nom `linkivi_event` (`type`, `event`, `screen_id`, `device_id`, `data`).

## La carte « Écrans Linkivi »

Une carte pour le tableau de bord, fournie par l'intégration. Après l'installation (ou une mise à jour), **redémarrez Home Assistant**, puis rechargez la page avec Ctrl+F5.

Si la carte n'apparaît pas toute seule (« Custom element doesn't exist »), déclarez-la une fois : Paramètres › Tableaux de bord › menu ⋮ › Ressources (mode avancé activé dans votre profil), puis ajoutez `/linkivi/linkivi-screens-card.js` en type **Module JavaScript**. Le fichier vient de l'intégration et se met à jour avec elle. Pour vérifier sans rien déclarer, ouvrez la console du navigateur (F12) et tapez `!!customElements.get("linkivi-screens-card")`.

Modifier le tableau de bord › Ajouter une carte › **Écrans Linkivi**. Elle trouve toute seule les écrans de l'intégration, avec leurs noms, aires et appareils ; un écran ajouté plus tard dans Linkivi y apparaît seul. Elle reprend les couleurs du thème (clair ou sombre), en français ou en anglais selon votre profil. En en-tête, un anneau et un résumé du parc (« 5 en ligne · 1 hors ligne »), avec « Tout allumer » et « Tout éteindre » pour les écrans affichés.

| Style | Rendu |
|---|---|
| `list` (par défaut) | « Verre » : une ligne givrée par écran sur un fond dégradé. Un médaillon dont la couleur dit l'état (vert allumé, bleu en veille, orange en cours, gris hors ligne), le redémarrage du player, le menu ⋮ (redémarrer ou éteindre l'appareil, avec confirmation) et un interrupteur lumineux « Écran ». |
| `cards` | « Écrans » : chaque écran est une petite télé dont l'état se lit sur l'écran (bleu et reflet avec un voyant qui bat, noir en veille, hachuré hors ligne, roue pendant une commande). Dessous : le nom, le bouton d'allumage rond, le redémarrage du player et le menu ⋮. Se met en colonnes selon la largeur. |

Sur chaque écran :

- **Liste diffusée** sous chaque écran : un clic la change, publiée aussitôt ; une bulle « Annuler » remet l'ancienne pendant 10 s. Pour un écran sans commandes, la liste passe à droite, en pastille.
- **Aperçu du direct** dans la télé (style `cards`) ou en vignette (style `list`), pour un écran allumé et en ligne : une nouvelle image toutes les `preview_interval` minutes (5 par défaut), seulement quand la carte est visible, car chaque image demande une capture à l'appareil.
- **Fenêtre d'un écran** (clic sur la télé ou la ligne) : grand aperçu, actualisé à l'ouverture puis chaque minute, liste diffusée, état, dernière connexion et commandes.
- **Alerte d'urgence** : bandeau rouge en tête de carte tant qu'une alerte est en cours, avec « Lever l'alerte » ; « Déclencher une alerte… » dans le menu ⋮ de la carte (appui maintenu 1,5 s), sur les écrans de la carte (filtre `screens`) ou sur tous. Réservé aux administrateurs de Home Assistant, sauf `emergency_for_all: true`.
- Options : `show_playlist`, `show_preview`, `preview_interval`, `show_emergency`, `emergency_for_all`.

Une commande montre « en cours » aussitôt (l'état confirmé arrive par le canal temps réel, en quelques secondes) ; si Linkivi refuse, sa raison s'affiche en notification. Les animations s'arrêtent si le système demande moins de mouvement.

```yaml
type: custom:linkivi-screens-card   # tout le reste est facultatif
title: Écrans Linkivi
style: list                         # list | cards
screens:                            # absent : tous les écrans (noms de Linkivi)
  - Rpi borne 01
  - Ecran photos
show_player_restart: true
show_device_actions: true           # le menu ⋮ (ou les boutons Appareil / Éteindre)
show_group_buttons: true            # Tout allumer / Tout éteindre
hide_offline: false
show_playlist: true                 # liste diffusée sous chaque écran
show_preview: true                  # aperçu du direct
preview_interval: 5                 # minutes entre deux images
show_emergency: true                # bandeau et menu de l'alerte d'urgence
emergency_for_all: false            # true : pas seulement les administrateurs
accent_color: "#2a86ee"             # couleur d'accent (bleu Linkivi par défaut)
```

L'éditeur visuel permet les mêmes réglages. Si la carte n'apparaît pas dans la liste, rechargez la page sans le cache ; sinon, vérifiez dans les journaux de Home Assistant que l'intégration Linkivi est bien démarrée.

## Afficher un message sur un écran

Deux actions, dans l'éditeur d'automatisations (Ajouter une action › Linkivi) ou dans Outils de développement › Actions.

| Action | Rôle |
|---|---|
| `linkivi.show_message` | Affiche un message par-dessus la diffusion des écrans choisis, puis la diffusion reprend avec le contenu suivant. |
| `linkivi.clear_display` | Retire le message tout de suite. |

Champs de `show_message` : `title` (60 caractères) ou `message` (300) au moins un des deux ; `look` : `information` (clair, par défaut) ou `attention` (ambre) ; `place` : `full` (plein écran, par défaut), `banner` (bandeau) ou `corner` (carte dans un coin, la diffusion continue) ; `corner` : `bottom_right` (défaut), `bottom_left`, `top_right` ou `top_left` ; `duration` en secondes, de 5 à 3600 (vide : 30 s, 15 s en coin) ; `wake` : réveille un écran en veille pour la durée du message ; `camera` : l'image d'une caméra de Home Assistant, ou `image_url` : une image à une adresse (lue par Home Assistant, 3 Mo au plus) ; `live` : l'image de la caméra est rafraîchie toutes les 2 s (mention « En direct ») ; `tag` : une carte de même étiquette remplace l'ancienne. Les écrans se choisissent comme n'importe quel appareil : un écran, une pièce (aire Home Assistant) ou plusieurs.

Règles : l'écran doit être **en ligne** (un message de sonnette qui arrive trop tard ne sert à rien) et **éveillé**, sauf avec `wake: true` ; en plein écran, un nouveau message remplace le précédent ; en coin, deux cartes au plus s'empilent (la plus ancienne réduite à son titre) ; sur un mur d'écrans, seul l'écran du coin choisi montre la carte ; une alerte d'urgence passe devant. L'écran ne contacte jamais la caméra : Home Assistant lit l'image et l'envoie à Linkivi. Si Linkivi refuse, Home Assistant affiche la raison de chaque écran.

```yaml
automation:
  - alias: Sonnette sur la télé du salon
    triggers:
      - trigger: state
        entity_id: binary_sensor.sonnette
        to: "on"
    actions:
      - action: linkivi.show_message
        target:
          area_id: salon
        data:
          title: Quelqu'un sonne au portail
          look: attention
          place: corner
          camera: camera.portail
          tag: sonnette
          duration: 20
```

Plus simple : chaque écran a une entité **Message** (`notify.<écran>_message`) et l'organisation une entité **Tous les écrans**, utilisables par `notify.send_message` et par tous les blueprints qui notifient :

```yaml
- action: notify.send_message
  target:
    entity_id: notify.salon_message
  data:
    title: Le lave-linge est terminé
    message: Programme 40°, 1 h 12
```

## Actions et conditions d'appareil

Dans l'éditeur d'automatisations, « Appareil » › un écran Linkivi propose, en plus des déclencheurs :

- **Actions** : afficher un message (en coin par défaut, avec l'image d'une caméra), effacer le message, changer de liste, éteindre ou rallumer l'écran, redémarrer le player, redémarrer l'appareil (si le matériel le permet), déclencher l'alerte d'urgence sur cet écran ;
- **Conditions** : l'écran est en ligne, hors ligne, en veille, allumé, diffuse telle liste ; une alerte d'urgence est en cours.


## Exemples

```yaml
# Éteindre les écrans de l'accueil quand le dernier part, les rallumer le matin
automation:
  - alias: Écrans de l'accueil éteints le soir
    trigger:
      - platform: state
        entity_id: binary_sensor.presence_batiment
        to: "off"
        for: "00:15:00"
    action:
      - action: switch.turn_off
        target:
          entity_id: switch.accueil_ecran

  - alias: Redémarrer le player chaque nuit
    trigger:
      - platform: time
        at: "03:30:00"
    action:
      - action: button.press
        target:
          entity_id: button.accueil_redemarrer_le_player
```

Si Linkivi refuse (écran hors ligne, commande déjà en cours, appareil non compatible), Home Assistant affiche la raison donnée par Linkivi.

## Sous le capot

L'intégration n'appelle que l'API publique de Linkivi (voir `/docs/api` sur votre serveur) :

| Appel | Accès | Usage |
|---|---|---|
| `POST /api/v1/ha/pair`, `POST /api/v1/ha/pair/token` | sans clé | Appairage par code : demande du code, puis relevé de la réponse toutes les 5 s (`202` en attente, `200` avec la clé, `403` refusé, `410` expiré). |
| `GET /api/v1/me` | `account:read` | Nom de l'organisation. |
| `DELETE /api/v1/me` | `account:read` | Révoque la clé, quand on supprime l'intégration. |
| `GET /api/v1/stream` (WebSocket) | `screens:read` | Canal temps réel : un état complet (`snapshot`), puis `screen.changed`, `screen.removed` et les événements ; `?after=<seq>` pour reprendre. |
| `GET /api/v1/stream/next` | `screens:read` | Le même canal en attente longue, si le WebSocket ne passe pas. |
| `GET /api/v1/screens` | `screens:read` | Relecture complète toutes les 5 min, par sécurité. Chaque écran liste dans `commands` ce que son matériel sait faire. |
| `POST /api/v1/screens/{id}/commands` | `screens:control` | `{"command": "restart-player" \| "reboot" \| "poweroff" \| "screen-off" \| "wake"}`, réponse `202`. |
| `POST /api/v1/screens/{id}/display` | `screens:control` | `{"title", "message", "look", "durationSeconds", "wake"}`, réponse `202`. |
| `DELETE /api/v1/screens/{id}/display` | `screens:control` | Retire le message. |
| `GET /api/v1/playlists`, `PUT /api/v1/screens/{id}/playlist` | `screens:read`, `screens:playlist` | Listes de l'organisation, et changement de la liste diffusée. |
| `POST /api/v1/screens/{id}/capture` | `screens:control` | Aperçu du direct (image de l'écran). |
| `GET /api/v1/emergency`, `POST /api/v1/emergency`, `DELETE /api/v1/emergency/{id}` | `emergency:read`, `emergency:write` | Alertes en cours, déclencher, lever. |
| `POST /api/v1/stream/up` | `screens:read` | Réponses de l'intégration aux demandes de Linkivi (états et images partagés). |

Sans Home Assistant, ces appels servent aussi depuis un script (`curl -H "Authorization: Bearer lkv_…"`).

## Versions

| Version | Nouveautés |
|---|---|
| **1.9.0** | Pochette d'un **lecteur multimédia** partagé, pour l'application **« En cours de lecture »** de Linkivi. |
| 1.8.1 | Réparation **« Redémarrage nécessaire »** après une mise à jour, avec un bouton qui redémarre Home Assistant. Huit **blueprints** et leurs automatisations équivalentes ([AUTOMATISATIONS.md](AUTOMATISATIONS.md)). |
| 1.8.0 | Place **Coin** (carte posée sur la diffusion), image d'une caméra ou d'une adresse, image en direct, étiquette ; entités **Message** et **Tous les écrans** (`notify`) ; capteurs **Batterie** et **En charge** ; actions et conditions d'appareil. |
| 1.7.2 | Bouton **Reconfigurer** : nouvelle autorisation par code sans supprimer l'intégration (par exemple pour obtenir l'urgence). |
| 1.7.1 | Tout sur tous les plans (commandes, messages, aperçu, urgence sans l'application du Store). Carte 2.0.1. |
| 1.7.0 | Carte « Écrans Linkivi » 2.0 : liste diffusée, aperçu du direct, fenêtre d'un écran, alerte d'urgence. |
| 1.6.0 | Partage des appareils de la maison avec les écrans de Linkivi, sans jeton ni relais. |
| 1.5 | Liste diffusée, état, aperçu du direct, urgence. |
| 1.4 | Connexion par code, temps réel, déclencheurs. |

## Pas encore essayé

Les entités ont été vues sur une vraie instance (six écrans). Le code Python n'est pas exécuté sur le poste de développement (pas de Python) : **les boutons, l'interrupteur, les actions, le bouton Reconfigurer, la carte et les nouveautés de la 1.8.0 (coin, image, notifications, batterie, actions et conditions d'appareil) n'ont pas encore tous été essayés dans un vrai Home Assistant**. Le serveur de Linkivi est couvert par des tests (`HaPairingTests`, `ScreenCommandsApiTests`) ; la carte a été essayée dans un faux Home Assistant.
