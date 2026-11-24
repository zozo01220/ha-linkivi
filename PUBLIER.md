# Publier l'intégration Linkivi (§302, lot 4 du §299)

Ce dossier `homeassistant/` devient la **racine** du dépôt public `zozo01220/ha-linkivi`. Le dépôt privé `Linkii.dev` reste la source : on y travaille, puis on publie.

## 1. Créer le dépôt public (une fois, par vous)

1. Sur github.com (compte `zozo01220`) : **New repository** › nom `ha-linkivi`, **Public**, sans README.
2. Dans le dépôt privé, publier le dossier `homeassistant/` seul, avec son historique :

```bash
git subtree split --prefix=homeassistant -b ha-linkivi-public
git push https://github.com/zozo01220/ha-linkivi.git ha-linkivi-public:main
```

Les publications suivantes : voir « Publier une nouvelle version » ci-dessous (script).

## Publier une nouvelle version : le script `deploy/publier-ha.ps1`

Le dépôt public n'est **pas** mis à jour par le push vers `main` : on le publie avec le script. Il remplace `git subtree split`, qui relit les 500 commits du dépôt privé et prend plusieurs minutes ; le script copie simplement le dossier et prend quelques secondes.

### Utilisation

1. **Mettre la version à jour** dans `custom_components/linkivi/manifest.json` (et la ligne de `README.md`), puis **commiter** : le script refuse de publier si `homeassistant/` a des changements non commités.
2. **Ouvrir PowerShell** et se placer dans le dépôt, jamais dans `C:WindowsSystem32` (PowerShell s'ouvre parfois là : Git répond « dubious ownership », ne pas ajouter d'exception `safe.directory`) :

```powershell
cd C:DEVEn-coursLinkii
```

3. **Voir d'abord ce qui sera publié**, sans rien envoyer :

```powershell
.deploypublier-ha.ps1 -DryRun
```

4. **Publier** (le script demande « o » pour confirmer avant d'envoyer) :

```powershell
.deploypublier-ha.ps1
```

5. **Créer la release** : à la main (le script donne l'adresse), ou en une fois avec la commande `gh` (GitHub CLI, à installer et connecter une fois avec `gh auth login`) :

```powershell
.deploypublier-ha.ps1 -Release -Notes "Ce qui change dans cette version"
```

6. **Dans Home Assistant** : HACS › Linkivi › menu ⋮ › Mettre à jour les informations › Télécharger › redémarrer. Si `blueprints/` a changé, ré-importer le blueprint (Paramètres › Automatisations › Blueprints).

Si PowerShell refuse d'exécuter le script (« l'exécution de scripts est désactivée ») : `powershell -ExecutionPolicy Bypass -File .deploypublier-ha.ps1`.

### Options

| Option | Effet |
|---|---|
| `-DryRun` | va jusqu'à la copie et liste les fichiers qui changeraient ; ni commit ni push |
| `-Version 1.14.2` | garde-fou : le script s'arrête si le manifeste ne dit pas exactement cette version |
| `-Release` | crée aussi la release `vX.Y.Z` avec `gh` |
| `-Notes "…"` | texte de la release (défaut : « Linkivi X.Y.Z ») |
| `-Yes` | ne demande pas confirmation |
| `-PublicDir "D:…"` | autre dossier pour le clone du dépôt public (défaut : `C:DEVha-linkivi-public`) |

### Ce que fait le script, étape par étape

1. **Version** : lit `version` dans `manifest.json` (ce sera l'étiquette `vX.Y.Z`) ; s'arrête si `-Version` est donnée et différente.
2. **Dépôt privé propre** : vérifie que `homeassistant/` n'a aucun changement non commité.
3. **Clone du dépôt public** : au premier lancement, clone `zozo01220/ha-linkivi` dans `C:DEVha-linkivi-public` ; ensuite, le remet exactement sur `origin/main` (`fetch` puis `reset --hard`). Ce clone est un miroir : ne jamais y travailler à la main, tout y est écrasé. Prévient si l'étiquette existe déjà.
4. **Copie** : `robocopy /MIR` rend le clone identique à `homeassistant/` (fichiers supprimés compris) ; `.git`, `__pycache__` et `*.pyc` sont ignorés.
5. **Changements** : `git add -A` puis liste des fichiers modifiés. S'il n'y en a aucun, le dépôt public est déjà à jour et le script s'arrête. Il vérifie aussi que le manifeste copié porte bien la version attendue. Avec `-DryRun`, il s'arrête ici.
6. **Commit et push** : demande confirmation, commit « Linkivi X.Y.Z » et push vers `main` du dépôt public.
7. **Vérification** : compare le commit de `main` chez GitHub (`git ls-remote`) à celui du clone ; s'ils diffèrent, erreur.
8. **Release** : avec `-Release` et `gh`, crée la release `vX.Y.Z` sur `main` ; sinon affiche l'adresse pour la créer. **Une étiquette seule ne suffit pas** : HACS ne propose que les *releases*, et la release doit être créée **après** le push (sinon elle pointe sur l'ancien contenu).

Le script n'écrit jamais dans le dépôt privé et ne force jamais le push.

### Ancienne méthode (si le script ne peut pas servir)

```powershell
cd C:DEVEn-coursLinkii
git branch -D ha-linkivi-public
git subtree split --prefix=homeassistant -b ha-linkivi-public
git push https://github.com/zozo01220/ha-linkivi.git ha-linkivi-public:main
```

Lente (tout l'historique est relu), puis release à créer à la main.

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
