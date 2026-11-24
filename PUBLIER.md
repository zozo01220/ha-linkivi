# Publier l'intégration Linkivi (§302, lot 4 du §299)

Ce dossier `homeassistant/` devient la **racine** du dépôt public `zozo01220/ha-linkivi`. Le dépôt privé `Linkii.dev` reste la source : on y travaille, puis on publie.

## 1. Créer le dépôt public (une fois, par vous)

1. Sur github.com (compte `zozo01220`) : **New repository** › nom `ha-linkivi`, **Public**, sans README.
2. Dans le dépôt privé, publier le dossier `homeassistant/` seul, avec son historique :

```bash
git subtree split --prefix=homeassistant -b ha-linkivi-public
git push https://github.com/zozo01220/ha-linkivi.git ha-linkivi-public:main
```

Les publications suivantes : voir « Publier une nouvelle version » ci-dessous.

## Publier une nouvelle version (à la main, pas à pas)

Le dépôt public n'est **pas** mis à jour par le push vers `main` : on le publie soi-même, dans cet ordre. Si l'étape 2 est oubliée, le push renvoie l'ancien contenu et la release pointe sur l'ancienne version (arrivé avec la 1.14.0).

1. **Tout commiter et pousser** dans le dépôt privé (la version est dans `custom_components/linkivi/manifest.json`, la ligne de `README.md` aussi).
2. **Se placer dans le dépôt**, jamais dans `C:WindowsSystem32` (PowerShell s'ouvre parfois là : Git répond « dubious ownership », ne pas ajouter d'exception `safe.directory`) :

```powershell
cd C:DEVEn-coursLinkii
```

3. **Refaire la branche** à partir du dossier `homeassistant/` (si Git dit que la branche existe déjà, la supprimer d'abord avec `git branch -D ha-linkivi-public`) :

```powershell
git subtree split --prefix=homeassistant -b ha-linkivi-public
```

4. **Vérifier** que la branche porte la bonne version :

```powershell
git show ha-linkivi-public:custom_components/linkivi/manifest.json | Select-String version
```

5. **Pousser** vers le dépôt public :

```powershell
git push https://github.com/zozo01220/ha-linkivi.git ha-linkivi-public:main
```

6. **Créer la release** sur github.com/zozo01220/ha-linkivi (voir ci-dessous), puis, dans Home Assistant : HACS › Linkivi › Mettre à jour, redémarrer.
7. **Blueprint** : si `blueprints/` a changé, le ré-importer dans Home Assistant (Paramètres › Automatisations › Blueprints).

Vérifier que le dépôt public a bien reçu la version : `git ls-remote https://github.com/zozo01220/ha-linkivi.git` doit montrer, pour `refs/heads/main`, le même numéro de commit que `git rev-parse ha-linkivi-public`.

## 2. Publier une version

1. Mettre `version` à jour dans `custom_components/linkivi/manifest.json` (ex. `1.5.0`).
2. Dans le dépôt public : **Releases › Draft a new release**, étiquette `v1.5.0` créée sur `main` **après** le push de l'étape 5 (étiquette et release se refont si elles ont été créées trop tôt : les supprimer, puis recréer), notes de version. **Indispensable** : HACS propose la dernière *Release*, pas la dernière étiquette ; une étiquette seule n'apparaît pas dans Home Assistant.
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
