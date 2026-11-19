# Linkivi : blueprints et automatisations prêtes à l'emploi

Huit cas d'usage, chacun sous deux formes :

- **le blueprint** : un clic sur le bouton « Importer », puis Paramètres › Automatisations › Blueprints › le blueprint › « Créer une automatisation » ;
- **l'automatisation équivalente** : à coller en YAML (Paramètres › Automatisations › Créer › menu ⋮ › « Modifier en YAML »), ou à refaire pas à pas dans l'éditeur visuel.

Remplacez les entités d'exemple (`binary_sensor.sonnette`, `sensor.salon_batterie`…) par les vôtres. Les écrans Linkivi se choisissent comme n'importe quel appareil : un écran, une pièce (`area_id`) ou plusieurs.

| Cas | Blueprint |
|---|---|
| [Sonnette sur les écrans](#1-sonnette-sur-les-écrans) | [![Importer](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fzozo01220%2Fha-linkivi%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flinkivi%2Fsonnette.yaml) |
| [Fin de cycle d'un appareil](#2-fin-de-cycle-dun-appareil) | [![Importer](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fzozo01220%2Fha-linkivi%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flinkivi%2Ffin-de-cycle.yaml) |
| [Fuite, fumée, CO : alerte d'urgence](#3-fuite-fumée-co--alerte-durgence) | [![Importer](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fzozo01220%2Fha-linkivi%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flinkivi%2Falerte-urgence.yaml) |
| [Écran allumé seulement quand il y a quelqu'un](#4-écran-allumé-seulement-quand-il-y-a-quelquun) | [![Importer](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fzozo01220%2Fha-linkivi%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flinkivi%2Fpresence-veille.yaml) |
| [Redémarrer un écran qui ne répond plus](#5-redémarrer-un-écran-qui-ne-répond-plus) | [![Importer](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fzozo01220%2Fha-linkivi%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flinkivi%2Fchien-de-garde.yaml) |
| [Batterie d'une tablette entre 20 et 80 %](#6-batterie-dune-tablette-entre-20-et-80-) | [![Importer](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fzozo01220%2Fha-linkivi%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flinkivi%2Fbatterie-tablette.yaml) |
| [Jour Tempo de demain](#7-jour-tempo-de-demain) | [![Importer](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fzozo01220%2Fha-linkivi%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flinkivi%2Ftempo.yaml) |
| [Mode invité](#8-mode-invité) | [![Importer](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fzozo01220%2Fha-linkivi%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flinkivi%2Finvites.yaml) |

Sans le bouton : Paramètres › Automatisations › Blueprints › « Importer un blueprint », et collez l'adresse du fichier, par exemple `https://github.com/zozo01220/ha-linkivi/blob/main/blueprints/automation/linkivi/sonnette.yaml`.

---

## 1. Sonnette sur les écrans

Quand on sonne, l'image de la caméra s'affiche en carte dans un coin des écrans du salon, sans couper la diffusion. Une nouvelle sonnerie remplace la carte (étiquette `sonnette`).

```yaml
alias: Sonnette sur les écrans
mode: restart
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
      corner: bottom_right
      duration: 30
      camera: camera.portail
      tag: sonnette
```

**Pas à pas dans l'éditeur visuel**
1. Déclencheur › **Entité** › **État** : `binary_sensor.sonnette`, « Vers » : Activé.
2. Action › chercher **Linkivi : Afficher un message**.
3. Cible : la pièce ou les écrans. Titre ; Aspect : Attention ; Emplacement : **Coin** ; Caméra : `camera.portail` ; Étiquette : `sonnette`.
4. Pour une image qui bouge : cocher **Image en direct** (rafraîchie toutes les 2 s).

---

## 2. Fin de cycle d'un appareil

La prise connectée du lave-linge mesure la puissance. Quand l'appareil a tourné puis retombe sous 5 W pendant 3 minutes, une carte s'affiche en coin.

```yaml
alias: Lave-linge terminé
mode: single
triggers:
  - trigger: numeric_state
    entity_id: sensor.lave_linge_puissance
    above: 20
actions:
  - wait_for_trigger:
      - trigger: numeric_state
        entity_id: sensor.lave_linge_puissance
        below: 5
        for:
          minutes: 3
    timeout:
      hours: 6
    continue_on_timeout: false
  - action: linkivi.show_message
    target:
      area_id: cuisine
    data:
      title: Le lave-linge est terminé
      message: Pensez à le vider.
      place: corner
```

**Pas à pas**
1. Déclencheur › **Entité** › **État numérique** : la puissance, « Au-dessus de » 20.
2. Action › **Attendre un déclencheur** › État numérique : la puissance, « En dessous de » 5, pendant 3 min ; délai d'attente 6 h, « Continuer après le délai » décoché.
3. Action › **Linkivi : Afficher un message**, Emplacement **Coin**.

Plus simple, si l'appareil a déjà un capteur « terminé » (beaucoup de lave-linge connectés) : un seul déclencheur sur ce capteur, puis l'action. Ou, pour un message à la fois sur le téléphone et sur l'écran : `notify.send_message` sur l'entité **Message** de l'écran, dans un groupe de notification.

---

## 3. Fuite, fumée, CO : alerte d'urgence

Le premier capteur qui passe à « on » déclenche l'alerte rouge plein écran sur **tous** les écrans (même en veille). Elle se lève quand tous les capteurs sont revenus à « off ».

```yaml
alias: Alerte fuite d'eau
mode: queued
triggers:
  - trigger: state
    entity_id:
      - binary_sensor.fuite_cuisine
      - binary_sensor.fuite_buanderie
    to: "on"
    id: start
  - trigger: state
    entity_id:
      - binary_sensor.fuite_cuisine
      - binary_sensor.fuite_buanderie
    to: "off"
    id: end
actions:
  - choose:
      - conditions:
          - condition: trigger
            id: start
        sequence:
          - action: linkivi.start_emergency
            data:
              title: Fuite d'eau
              message: Une fuite d'eau est détectée. Coupez l'arrivée d'eau.
      - conditions:
          - condition: trigger
            id: end
          - condition: state
            entity_id:
              - binary_sensor.fuite_cuisine
              - binary_sensor.fuite_buanderie
            state: "off"
        sequence:
          - action: linkivi.end_emergency
```

**Pas à pas**
1. Deux déclencheurs **État** sur les mêmes capteurs : l'un « Vers Activé » (identifiant `start`), l'autre « Vers Désactivé » (identifiant `end`). L'identifiant se règle dans le menu ⋮ du déclencheur.
2. Action › **Choisir** : option 1, condition « Déclenché par » `start` → **Linkivi : Déclencher l'alerte d'urgence** (sans cible : tous les écrans) ; option 2, conditions « Déclenché par » `end` et **État** de tous les capteurs = Désactivé → **Linkivi : Lever l'alerte**.

Une alerte pour un seul écran : dans l'éditeur, « Appareil » › l'écran › action **Déclencher l'alerte d'urgence sur …**.

---

## 4. Écran allumé seulement quand il y a quelqu'un

```yaml
alias: Écran du salon selon la présence
mode: restart
triggers:
  - trigger: state
    entity_id: binary_sensor.salon_presence
    to: "on"
    id: here
  - trigger: state
    entity_id: binary_sensor.salon_presence
    to: "off"
    for:
      minutes: 10
    id: empty
actions:
  - choose:
      - conditions:
          - condition: trigger
            id: here
        sequence:
          - action: switch.turn_on
            target:
              entity_id: switch.salon_ecran
      - conditions:
          - condition: trigger
            id: empty
        sequence:
          - action: switch.turn_off
            target:
              entity_id: switch.salon_ecran
```

**Pas à pas** (sans YAML, par l'appareil)
1. Déclencheur **État** : la présence, « Vers Détecté » (identifiant `here`) ; deuxième déclencheur : « Vers Non détecté » pendant 10 min (identifiant `empty`).
2. Action › **Choisir** : `here` → « Appareil » › l'écran › **Rallumer l'écran** ; `empty` → « Appareil » › l'écran › **Éteindre l'écran**.

Allumer = réveil d'une heure, puis les plages de veille de Linkivi reprennent la main ; avec un détecteur qui reste « on », le réveil se renouvelle à chaque passage.

---

## 5. Redémarrer un écran qui ne répond plus

```yaml
alias: Chien de garde de l'écran de l'entrée
mode: single
max_exceeded: silent
triggers:
  - trigger: state
    entity_id: binary_sensor.entree_en_ligne
    to: "off"
    for:
      minutes: 10
actions:
  - action: switch.turn_off
    target:
      entity_id: switch.prise_ecran_entree
  - delay:
      seconds: 15
  - action: switch.turn_on
    target:
      entity_id: switch.prise_ecran_entree
  - action: notify.send_message
    target:
      entity_id: notify.mon_telephone
    data:
      message: L'écran de l'entrée ne répondait plus, sa prise a été coupée puis rallumée.
  - wait_for_trigger:
      - trigger: state
        entity_id: binary_sensor.entree_en_ligne
        to: "on"
    timeout:
      hours: 1
```

**Pas à pas**
1. Déclencheur : « Appareil » › l'écran › **… ne répond plus** (ou **État** du capteur « En ligne » vers Déconnecté pendant 10 min).
2. Actions : prise **Éteindre**, **Attendre** 15 s, prise **Allumer**, puis une notification si vous le voulez.

---

## 6. Batterie d'une tablette entre 20 et 80 %

```yaml
alias: Charge de la tablette de la cuisine
mode: single
triggers:
  - trigger: numeric_state
    entity_id: sensor.cuisine_batterie
    below: 20
    id: charge
  - trigger: numeric_state
    entity_id: sensor.cuisine_batterie
    above: 80
    id: stop
actions:
  - choose:
      - conditions:
          - condition: trigger
            id: charge
        sequence:
          - action: switch.turn_on
            target:
              entity_id: switch.prise_chargeur_cuisine
      - conditions:
          - condition: trigger
            id: stop
        sequence:
          - action: switch.turn_off
            target:
              entity_id: switch.prise_chargeur_cuisine
```

**Pas à pas** : deux déclencheurs **État numérique** sur le capteur « Batterie » de l'écran (en dessous de 20, identifiant `charge` ; au-dessus de 80, identifiant `stop`), puis **Choisir** : allumer ou éteindre la prise.

Le capteur « Batterie » n'existe que pour les smartphones et tablettes Android ; « En charge » dit si la prise fait bien son travail.

---

## 7. Jour Tempo de demain

À 19 h, si le capteur de couleur du lendemain dit « Rouge » ou « Blanc », un message reste une heure en coin sur les écrans.

```yaml
alias: Jour Tempo de demain
mode: single
triggers:
  - trigger: time
    at: "19:00:00"
conditions:
  - condition: state
    entity_id: sensor.tempo_demain
    state:
      - Rouge
      - Blanc
actions:
  - action: linkivi.show_message
    target:
      area_id: cuisine
    data:
      title: "Demain : jour {{ states('sensor.tempo_demain') | lower }}"
      message: Lancez les machines avant 6 h demain matin.
      look: attention
      place: corner
      duration: 3600
      tag: tempo
```

**Pas à pas**
1. Déclencheur **Heure** : 19:00.
2. Condition **État** : le capteur de couleur, état Rouge ou Blanc (tels que votre intégration les écrit : regardez l'état du capteur dans Outils de développement › États).
3. Action **Linkivi : Afficher un message**, Emplacement Coin (ou Bandeau), Durée 3600.

Le même schéma sert pour Ecowatt, les heures creuses ou un surplus solaire (« C'est le moment de lancer une machine »).

---

## 8. Mode invité

```yaml
alias: Écrans en mode invité
mode: queued
triggers:
  - trigger: state
    entity_id: input_boolean.mode_invite
    to: "on"
    id: arrive
  - trigger: state
    entity_id: input_boolean.mode_invite
    to: "off"
    id: leave
actions:
  - action: linkivi.show_list
    target:
      area_id: entree
    data:
      playlist: "{{ 'Invités' if trigger.id == 'arrive' else 'Accueil' }}"
```

**Pas à pas**
1. Créez dans Linkivi une liste « Invités » (bienvenue, QR du Wi-Fi invité, consignes, heure de départ).
2. Déclencheurs **État** sur le mode invité (`arrive` vers Activé, `leave` vers Désactivé).
3. Action **Choisir** : `arrive` → « Appareil » › l'écran › **Changer la liste** › Invités ; `leave` → **Changer la liste** › Accueil.

Avec une location courte durée : remplacez le mode invité par un calendrier de réservations (iCal d'Airbnb ou d'un autre site, intégration « Calendrier distant ») : il passe à « on » pendant chaque séjour. Une composition Linkivi peut afficher le nom des voyageurs si vous partagez une entité texte (`input_text`) avec Linkivi.
