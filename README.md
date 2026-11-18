# Linkivi pour Home Assistant

Voir et commander ses écrans Linkivi depuis Home Assistant : redémarrer le player, redémarrer l'appareil, éteindre l'appareil, éteindre l'écran, le réveiller, et **y afficher un message** (sonnette, lave-linge terminé…).
Chaque écran devient un **appareil** Home Assistant. À ne pas confondre avec l'intégration Home Assistant **de** Linkivi (lire et commander les appareils d'une maison sur les écrans) : ici, c'est l'inverse.

Prérequis : Home Assistant 2024.11 ou plus récent. **Tous les plans** de Linkivi : voir les écrans, leur état et leurs événements. **Plan Pro** : commander les écrans et y afficher un message (sur les autres plans, l'intégration ne crée ni les boutons, ni l'interrupteur « Écran », ni les actions).

## Installer

1. **Dans Home Assistant** : par HACS (menu ⋮ › Dépôts personnalisés › `https://github.com/zozo01220/ha-linkivi`, catégorie Intégration, une fois le dépôt public créé, voir `PUBLIER.md`), ou à la main : copiez le dossier `custom_components/linkivi` dans le dossier `config/custom_components/` de Home Assistant, puis redémarrez Home Assistant.
2. Paramètres › Appareils et services › Ajouter une intégration › **Linkivi** › **Se connecter avec un code** : adresse de votre Linkivi (par exemple `https://linkivi.duckdns.org`).
3. Home Assistant affiche un **lien** et un **code** (8 lettres, `WDJB-MJHT`), valable 10 minutes. Ouvrez le lien : Linkivi s'ouvre (connectez-vous si besoin), vérifiez que le code est le même, choisissez l'organisation si vous en gérez plusieurs, puis **Autoriser**.
4. Home Assistant reçoit sa clé tout seul : les écrans apparaissent en quelques secondes.

Qui peut autoriser : un administrateur de l'organisation, ou un membre qui publie **sans approbation**. Home Assistant agit ensuite au nom de cette personne, sans approbation. L'accès se retire dans Linkivi, Applications › Home Assistant › « Accès de Home Assistant » ; supprimer l'intégration dans Home Assistant le retire aussi.

**Avancé** : « Coller une clé d'API » marche toujours avec une clé du modèle « Home Assistant » créée dans « API et webhooks » (plan Pro).

**Mise à jour depuis la 1.3** : l'entrée existante garde sa clé collée à la main et passe au temps réel ; rien à refaire.

Les écrans ajoutés plus tard dans Linkivi apparaissent seuls, **en direct** (voir « Temps réel »).

## Ce que chaque écran offre

| Entité | Type | Rôle |
|---|---|---|
| **En ligne** | capteur binaire | L'écran a donné de ses nouvelles ces 90 dernières secondes. Attributs : état, dernier contact, aire, zone, liste, résolution. |
| **Écran** | interrupteur | Allumé = éveillé. Éteindre = veille manuelle jusqu'au réveil. Allumer = réveil d'**une heure**, puis les plages de veille et les calendriers reprennent la main (comme « Réveiller » dans Linkivi). Marche aussi quand l'écran est hors ligne : la consigne est lue à son retour. |
| **Redémarrer le player** | bouton | Relance l'application d'affichage. |
| **Redémarrer l'appareil** | bouton | Redémarre le PC, le Raspberry Pi ou l'appareil Android. |
| **Éteindre l'appareil** | bouton | Éteint l'appareil. **Linkivi ne peut pas le rallumer** : il faut le bouton ou le courant. |

Un bouton n'existe que si le matériel sait faire la commande :

| Appareil | Player | Écran | Redémarrer | Éteindre |
|---|---|---|---|---|
| Windows, Raspberry Pi | oui | oui | oui | oui |
| Android, Android TV | oui | oui | seulement si l'app est propriétaire de l'appareil (`dpm set-device-owner`) | jamais |
| Navigateur | oui | oui | non | non |

Un écran de **mur** se commande en entier : un ordre sur un écran du mur part sur tous.

Depuis la 1.5 :

| Entité | Type | Rôle |
|---|---|---|
| **Liste diffusée** | liste de choix | La liste de lecture de l'écran. En choisir une autre la publie aussitôt, sans approbation. Tous les plans. Pas pour un écran de mur, une borne ou un écran Home Assistant. |
| **État** | capteur | En ligne, hors ligne, mise à jour, en veille ou en pause. |
| **Dernière connexion** | capteur (désactivé par défaut) | Dernier contact de l'écran. |
| **Aperçu du direct** | caméra | Ce que l'écran affiche (Pro, players Android et Raspberry Pi). Une nouvelle image est demandée au plus toutes les 60 s quand on la regarde. Un écran portrait peut arriver couché. |
| **Urgence en cours** | capteur binaire, appareil « Organisation » | Une alerte d'urgence est en cours (si l'intégration « Alerte d'urgence » est installée dans Linkivi). |

Actions : `linkivi.show_list` (`playlist` : nom de la liste), `linkivi.start_emergency` (`title` 40 caractères, `message` 300 ; sans cible, sur tous les écrans) et `linkivi.end_emergency` (lève toutes les alertes en cours). Une entrée reliée avant la 1.5 n'a pas les accès « liste » et « urgence » : supprimez l'intégration puis rajoutez-la avec un code.

## Montrer les appareils de la maison sur les écrans (1.6)

Dans Linkivi, Applications › Home Assistant › « Par l'intégration Linkivi » (conseillé). Puis, dans Home Assistant : Paramètres › Appareils et services › Linkivi › **Configurer** › « Partager avec Linkivi » : des pièces, des libellés ou des entités, et « Permettre aux écrans de commander ces appareils » (non par défaut). Les serrures et les alarmes ne se partagent qu'une à une. Linkivi ne garde alors **aucun jeton** de votre Home Assistant et n'a plus besoin du relais : il demande les états, l'historique et les images des caméras à l'intégration, qui ne répond que pour ce qui est partagé.

Déjà relié en direct ou par le relais ? Le bandeau « Passer par l'intégration » de Applications › Home Assistant fait la bascule dès que toutes les entités utilisées par vos écrans sont partagées ; l'ancien jeton est alors oublié.

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

**Depuis la carte 2.0 (intégration 1.7)** :

- **Liste diffusée** sous chaque écran : un clic la change, publiée aussitôt ; une bulle « Annuler » remet l'ancienne pendant 10 s. Sans le Pro, la liste passe à droite, en pastille.
- **Aperçu du direct** dans la télé (style ) ou en vignette (style ), pour un écran allumé et en ligne : une nouvelle image toutes les  minutes (5 par défaut), seulement quand la carte est visible, car chaque image demande une capture à l'appareil.
- **Fenêtre d'un écran** (clic sur la télé ou la ligne) : grand aperçu, actualisé à l'ouverture puis chaque minute, liste diffusée, état, dernière connexion et commandes.
- **Alerte d'urgence** : bandeau rouge en tête de carte tant qu'une alerte est en cours, avec « Lever l'alerte » ; « Déclencher une alerte… » dans le menu ⋮ de la carte (appui maintenu 1,5 s), sur les écrans de la carte (filtre ) ou sur tous. Réservé aux administrateurs de Home Assistant, sauf .
- Options : , , , , .

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
accent_color: "#2a86ee"             # couleur d'accent (bleu Linkivi par défaut)
```

L'éditeur visuel permet les mêmes réglages. Si la carte n'apparaît pas dans la liste, rechargez la page sans le cache ; sinon, vérifiez dans les journaux de Home Assistant que l'intégration Linkivi est bien démarrée.

## Afficher un message sur un écran

Deux actions, dans l'éditeur d'automatisations (Ajouter une action › Linkivi) ou dans Outils de développement › Actions.

| Action | Rôle |
|---|---|
| `linkivi.show_message` | Affiche un message par-dessus la diffusion des écrans choisis, puis la diffusion reprend avec le contenu suivant. |
| `linkivi.clear_display` | Retire le message tout de suite. |

Champs de `show_message` : `title` (60 caractères) ou `message` (300) au moins un des deux ; `look` : `information` (clair, par défaut) ou `attention` (ambre) ; `duration` en secondes, de 5 à 3600 (30 par défaut) ; `wake` : réveille un écran en veille pour la durée du message. Les écrans se choisissent comme n'importe quel appareil : un écran, une pièce (aire Home Assistant) ou plusieurs.

Règles : l'écran doit être **en ligne** (un message de sonnette qui arrive trop tard ne sert à rien) et **éveillé**, sauf avec `wake: true` ; un nouveau message remplace le précédent ; une alerte d'urgence passe devant. Si Linkivi refuse, Home Assistant affiche la raison de chaque écran.

```yaml
automation:
  - alias: Annoncer un visiteur
    trigger:
      - platform: state
        entity_id: binary_sensor.sonnette
        to: "on"
    action:
      - action: linkivi.show_message
        target:
          area_id: accueil
        data:
          title: Un visiteur est à l'accueil
          message: Merci d'aller l'accueillir
          duration: 30
```

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
| `GET /api/v1/me` | `account:read` | Nom de l'organisation et `pro` (commandes et messages permis). |
| `DELETE /api/v1/me` | `account:read` | Révoque la clé, quand on supprime l'intégration. |
| `GET /api/v1/stream` (WebSocket) | `screens:read` | Canal temps réel : un état complet (`snapshot`), puis `screen.changed`, `screen.removed` et les événements ; `?after=<seq>` pour reprendre. |
| `GET /api/v1/stream/next` | `screens:read` | Le même canal en attente longue, si le WebSocket ne passe pas. |
| `GET /api/v1/screens` | `screens:read` | Relecture complète toutes les 5 min, par sécurité. Chaque écran liste dans `commands` ce que son matériel sait faire. |
| `POST /api/v1/screens/{id}/commands` | `screens:control` | `{"command": "restart-player" \| "reboot" \| "poweroff" \| "screen-off" \| "wake"}`, réponse `202`. |
| `POST /api/v1/screens/{id}/display` | `screens:control` | `{"title", "message", "look", "durationSeconds", "wake"}`, réponse `202`. |
| `DELETE /api/v1/screens/{id}/display` | `screens:control` | Retire le message. |

Sans Home Assistant, ces appels servent aussi depuis un script (`curl -H "Authorization: Bearer lkv_…"`).

## Pas encore essayé

**Version 1.4 (connexion par code, temps réel, déclencheurs)** : jamais lancée dans un vrai Home Assistant. Le code Python n'a pas été exécuté (pas de Python sur le poste de développement). Le serveur est couvert par des tests (`HaPairingTests`, dont le WebSocket et l'attente longue), pas encore à travers le vrai proxy du serveur.

Les entités de l'intégration ont été vues sur une vraie instance (six écrans). En revanche, le code Python n'a jamais été exécuté sur le poste de développement (pas de Python) et **les boutons, l'interrupteur et l'action « Afficher un message » n'ont pas encore été essayés en vrai** (le serveur et l'affichage du message dans le player le sont par des tests et un essai dans le navigateur, pas sur un vrai écran) ; la carte, elle, a été essayée dans un faux Home Assistant (liste, cartes, menu, confirmations, erreurs, filtres) mais **pas dans le vrai** : l'enregistrement par l'intégration, l'éditeur visuel et le rendu sur votre thème sont à vérifier. L'API de Linkivi est couverte par des tests (`ScreenCommandsApiTests`).
