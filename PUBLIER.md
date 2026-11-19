# Publier l'intégration Linkivi (§302, lot 4 du §299)

Ce dossier `homeassistant/` devient la **racine** du dépôt public `zozo01220/ha-linkivi`. Le dépôt privé `Linkii.dev` reste la source : on y travaille, puis on publie.

## 1. Créer le dépôt public (une fois, par vous)

1. Sur github.com (compte `zozo01220`) : **New repository** › nom `ha-linkivi`, **Public**, sans README.
2. Dans le dépôt privé, publier le dossier `homeassistant/` seul, avec son historique :

```bash
git subtree split --prefix=homeassistant -b ha-linkivi-public
git push https://github.com/zozo01220/ha-linkivi.git ha-linkivi-public:main
```

Les publications suivantes : les deux mêmes commandes (la branche est refaite à chaque fois).

## 2. Publier une version

1. Mettre `version` à jour dans `custom_components/linkivi/manifest.json` (ex. `1.5.0`).
2. Dans le dépôt public : **Releases › Draft a new release**, étiquette `v1.5.0`, notes de version. **Indispensable** : HACS propose la dernière *Release*, pas la dernière étiquette ; une étiquette seule n'apparaît pas dans Home Assistant.
3. Les contrôles **hassfest** et **HACS** tournent tout seuls (`.github/workflows/validate.yml`) : ils doivent être verts.

## 3. Installer par HACS (chez un utilisateur)

HACS › menu ⋮ › **Dépôts personnalisés** › `https://github.com/zozo01220/ha-linkivi`, catégorie **Intégration** › Télécharger › redémarrer Home Assistant. Les mises à jour arrivent ensuite par HACS.

## 4. Plus tard : le magasin HACS par défaut

- Logo dans le dépôt `home-assistant/brands` (`custom_integrations/linkivi/icon.png`, 256 × 256, et `icon@2x.png`).
- Une demande d'ajout au dépôt `hacs/default`, contrôles verts, au moins une version publiée.

## 5. Plus tard : Home Assistant Core

À faire avant la demande (rien de cela n'est commencé) :

- **Python sur le poste de développement** : sans lui, rien ne peut être essayé ni testé ici.
- Une bibliothèque à part sur PyPI (`python-linkivi`, nom libre au 18 nov. 2026) : `api.py` et le canal de `stream.py`.
- Des tests `pytest` (l'ajout de l'intégration entièrement couvert, les entités, les actions).
- Les textes source en anglais dans `strings.json`, le français dans `translations/fr.json`, des messages d'erreur traduisibles.
- La carte « Écrans Linkivi » sortie de l'intégration (Core n'accepte pas de carte) : dépôt `zozo01220/linkivi-screens-card`, type « plugin » de HACS.
- Le niveau Bronze de l'échelle de qualité, la documentation sur home-assistant.io, puis la revue par l'équipe Home Assistant.
