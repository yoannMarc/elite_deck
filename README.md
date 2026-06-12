# ◈ Elite Deck

Terminal second écran **et** boîtier de macros pour Elite Dangerous, en un seul
projet Python moderne. Affiche la télémétrie du jeu en temps réel sur n'importe
quel appareil (PC, **tablette**, téléphone) et permet de déclencher des actions
du jeu (train, armes, énergie…) depuis l'écran tactile.

```
PC (jeu)                                      Tablette / navigateur
┌────────────────────────────────┐           ┌──────────────────────┐
│ ingest → lit les fichiers JSON  │           │  Client web          │
│ core   → GameState typé         │── snap ──▶│  • télémétrie live   │
│ macros → envoie les touches     │── patch ─▶│  • boutons macro      │
│ server → aiohttp WS + HTTP      │◀─ macro ──│  • responsive tactile │
│ integrations → EDSM / FDevIDs   │           └──────────────────────┘
│   (anticipé, désactivé)         │
└────────────────────────────────┘
```

Un appui sur un bouton de la tablette envoie un message WebSocket ; le PC
exécute la frappe clavier dans le jeu. La tablette n'a aucune dépendance : c'est
une page web.

---

## Prérequis

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** — gestionnaire d'environnement Python (remplace pip/venv)
- **[task](https://taskfile.dev)** — task runner (optionnel mais recommandé)

---

## Installation

### 1. Installer uv (si absent)

**Windows (PowerShell) :**
```powershell
winget install astral-sh.uv
```

**macOS / Linux :**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Vérifier :
```bash
uv --version
```

---

### 2. Installer les dépendances du projet

```bash
# Cœur uniquement (affichage tablette, lecture journaux)
uv sync

# + envoi de touches clavier (sur le PC qui fait tourner Elite Dangerous)
uv sync --extra macros

# Tout (dev, lint, tests, macros)
uv sync --all-extras
```

> **Note :** `uv sync` crée automatiquement le virtualenv `.venv/` dans le dossier projet.

---

### 3. Installer task (si absent)

**Windows :**
```powershell
winget install Task.Task
```

**macOS :**
```bash
brew install go-task/tap/go-task
```

**Linux :**
```bash
sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b ~/.local/bin
```

Vérifier :
```bash
task --version
```

---

## Lancement

### Via task (recommandé)

```bash
task          # lance le serveur + ouvre http://localhost:3300
task run      # identique
task run:dev  # mode verbose (logs détaillés)
```

### Via uv directement

```bash
uv run python -m elite_deck
uv run python -m elite_deck --verbose
uv run python -m elite_deck --config config.toml
```

**Depuis la tablette (même réseau Wi-Fi) :** `http://<ip-du-pc>:3300`

---

## Commandes task disponibles

| Commande | Description |
|---|---|
| `task` / `task run` | Lance le serveur et ouvre le navigateur |
| `task run:dev` | Lance en mode verbose |
| `task install` | `uv sync --all-extras` (install complète) |
| `task test` | Lance pytest |
| `task lint` | Ruff check (lint) |
| `task fmt` | Ruff format + fix automatique |

---

## Configuration

Copier l'exemple et l'adapter :

```bash
cp config.example.toml config.toml
```

Le fichier `config.toml` est **optionnel** — sans lui, les valeurs par défaut s'appliquent.
Il est ignoré par git (ajouté au `.gitignore`).

### Référence complète

```toml
[server]
host = "0.0.0.0"   # 0.0.0.0 = accessible depuis la tablette sur le réseau local
                   # "127.0.0.1" = local uniquement
port = 3300        # port HTTP + WebSocket

[ingest]
journal_dir = ""         # vide = auto-détection (Saved Games d'Elite Dangerous)
                         # exemple Windows : "C:/Users/Toi/Saved Games/Frontier Developments/Elite Dangerous"
replay_history = true    # rejoue les événements du dernier fichier journal au démarrage
poll_interval = 0.4      # intervalle de polling des fichiers JSON (secondes)

[integrations]
edsm_enabled    = false  # données système via EDSM (anticipé, non implémenté)
fdevids_enabled = false  # noms lisibles via FDevIDs (anticipé, non implémenté)

# Surcharge des raccourcis clavier.
# Les touches ici doivent correspondre exactement à celles configurées
# dans Elite Dangerous → Options → Commandes.
[keybinds]
landing_gear  = "g"
hardpoints    = "u"
cargo_scoop   = "home"
lights        = "insert"
analysis_mode = "f7"
sys_power     = "f1"
eng_power     = "f2"
wep_power     = "f3"
# Codes virtuels (touches absentes du clavier, ex. F13-F24) :
# silent_running = "vk:135"       # F24
# avec modificateurs :
# deploy_fighters = "ctrl+f5"
```

### Passer une config en argument

```bash
task run -- --config mon_profil.toml
uv run python -m elite_deck --config mon_profil.toml --port 3301
```

---

## Architecture

```
src/back/
├── __main__.py          ← point d'entrée CLI
├── app.py               ← racine de composition (câblage)
├── config.py            ← config typée (TOML)
├── core/
│   ├── models.py        ← GameState typé (+ slot d'enrichissement)
│   ├── flags.py         ← décodage Status.json
│   └── store.py         ← agrégation + pub/sub + diffs
├── ingest/
│   └── watcher.py       ← lecture async des fichiers du jeu + rotation
├── macros/
│   ├── keyspec.py       ← représentation riche d'une touche (char/nom/vk/scan)
│   ├── engine.py        ← envoi de touches (backends pynput / scancode / null)
│   ├── capture.py       ← détection d'une touche (listener PC, async)
│   ├── store.py         ← persistance des raccourcis (JSON)
│   └── registry.py      ← définitions de macros
├── server/
│   └── app.py           ← aiohttp : HTTP + WebSocket (état ↔ macros)
├── integrations/        ← ANTICIPÉ (stub, désactivé)
│   ├── base.py          ← Protocol DataProvider + manager
│   ├── edsm.py          ← provider EDSM (stub)
│   └── fdevids.py       ← provider FDevIDs (stub)
└── web/
```

Principes appliqués :
- **src layout** + `pyproject.toml` PEP 621
- **type hints** stricts partout, `from __future__ import annotations`
- **async-first** : un seul event loop pour ingestion + serveur
- **inversion de dépendances** : tout le câblage dans `app.py`, le reste dépend
  d'abstractions (`Protocol`, backends injectables)
- **ruff** (lint+format) et **mypy --strict** configurés
- backends et providers **injectables** → testables sans jeu ni matériel

---

## Macros

Définies dans `macros/registry.py`. Chaque macro a un identifiant stable, un
libellé, une touche (`KeySpec`) et, si pertinent, un `status_flag` qui allume le
bouton quand l'action est active dans le jeu (ex. train sorti).

### Configuration des raccourcis depuis la tablette

Le bouton **⚙ Configurer** passe le deck en mode configuration. Un appui sur une
macro ouvre alors une fenêtre permettant de redéfinir sa touche de deux façons :

1. **Détection** — « Appuyer sur une touche » : un listener démarre sur le PC,
   la prochaine touche pressée (avec ses modificateurs) est capturée et
   convertie en `KeySpec`. La capture a lieu sur le PC, pas dans le navigateur,
   car la touche doit être détectable par Elite Dangerous.
2. **Saisie de code / nom** — pour définir une touche **absente du clavier**
   mais détectable par ED. On saisit :
   - un caractère : `g`
   - un nom : `home`, `f7`, `numpad_0`
   - un **code virtuel** : `vk:135` (= F24)
   - avec modificateurs (Ctrl / Shift / Alt)

Le cas d'usage central est **F13-F24** : ED les détecte, presque aucun clavier
ne les a, donc aucun conflit avec un raccourci existant. Des boutons rapides
(F13…F16) sont fournis.

Les raccourcis modifiés sont **persistés** (`keybinds.json` dans le dossier de
config) et **diffusés** à tous les clients connectés. Ils doivent correspondre à
ceux configurés dans Elite Dangerous (Options → Commandes).

### Représentation d'une touche : `KeySpec`

```python
KeySpec(char="g")                          # caractère
KeySpec(name="home")                       # touche nommée
KeySpec(vk=135, modifiers=["ctrl"])        # code virtuel (Ctrl+F24)
KeySpec.parse("ctrl+shift+g")             # depuis une chaîne
```

### Backends d'envoi

Abstraits derrière un `Protocol` :
- `PynputBackend` (défaut) — envoi par VK, multiplateforme.
- `ScanCodeBackend` — envoi par **code de scan** via SendInput (Windows). Plus
  fiable pour les jeux DirectInput comme ED, qui lisent souvent les scan codes
  plutôt que les VK injectés. À activer si certaines touches ne « passent » pas.
- `NullBackend` — factice (tests, headless).

---

## Intégrations externes (anticipées)

La couche `integrations/` est **prête mais non implémentée**. Elle définit un
`Protocol DataProvider` et un manager qui interroge en parallèle les providers
activés, puis injecte les résultats dans `GameState.enrichment` — sans toucher
au noyau.

- **EDSM** (https://www.edsm.net/en/api-v1) : données système (corps, stations,
  valeur d'exploration). Stub dans `integrations/edsm.py`, avec les endpoints et
  la logique de cache documentés.
- **FDevIDs** (https://github.com/EDCD/FDevIDs) : CSV de correspondance
  identifiants internes → noms lisibles (vaisseaux, marchandises). Stub dans
  `integrations/fdevids.py`.

Pour activer plus tard : implémenter `enrich`, passer `enabled=True` (ou via la
config), aucun changement ailleurs.

---

## Tests

```bash
task test              # pytest
task lint              # ruff check
task fmt               # ruff format + fix

# Ou directement :
uv run pytest
uv run ruff check src tests
uv run mypy src
```

---

## Légal

Lit uniquement les fichiers de log écrits publiquement par le jeu dans le
dossier Saved Games. Aucune injection, aucun hook mémoire, aucune modification
du jeu. Non affilié à Frontier Developments.
