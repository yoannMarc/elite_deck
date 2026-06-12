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

## Pourquoi le web et pas tkinter ?

L'affichage cible est une **tablette**. tkinter est cantonné au bureau et ne se
diffuse pas sur le réseau. Un client web servi par le backend est accessible
depuis n'importe quel appareil, tactile et responsive par nature, et découple
proprement l'interface du moteur — donc plus maintenable et évolutif.

---

## Installation

Avec [uv](https://docs.astral.sh/uv/) (recommandé) :

```bash
uv sync                          # cœur seul
uv sync --extra macros           # + envoi de touches (sur le PC du jeu)
uv sync --all-extras             # tout (dev, intégrations…)
```

Ou pip :

```bash
pip install -e ".[macros]"
```

---

## Lancement

```bash
# Sur le PC qui fait tourner Elite Dangerous
python -m elite_deck --host 0.0.0.0

# Puis sur la tablette (même Wi-Fi) : http://<ip-du-pc>:3300
```

Options :

```bash
python -m elite_deck --config config.toml
python -m elite_deck --journal-dir "C:/.../Elite Dangerous"
python -m elite_deck --port 3300 --no-replay -v
```

Copie `config.example.toml` → `config.toml` pour personnaliser les raccourcis,
le port, et (plus tard) activer les intégrations.

---

## Architecture

```
src/elite_deck/
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
│   ├── engine.py        ← envoi de touches (backend abstrait)
│   └── registry.py      ← définitions de macros
├── server/
│   └── app.py           ← aiohttp : HTTP + WebSocket (état ↔ macros)
├── integrations/        ← ANTICIPÉ (stub, désactivé)
│   ├── base.py          ← Protocol DataProvider + manager
│   ├── edsm.py          ← provider EDSM (stub)
│   └── fdevids.py       ← provider FDevIDs (stub)
└── web/
    └── index.html       ← client tablette
```

Principes appliqués (standards Python 2026) :
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
libellé, un raccourci (configurable) et, si pertinent, un `status_flag` qui
allume le bouton quand l'action est active dans le jeu (ex. train sorti).

Les keybinds **ne sont jamais exposés** au client : la tablette envoie un
identifiant de macro, le serveur résout le raccourci et l'exécute. Les
raccourcis doivent correspondre à ceux configurés dans Elite Dangerous.

Ajouter une macro = ajouter une entrée dans `DEFAULT_MACROS`. Le bouton apparaît
automatiquement sur la tablette.

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
pytest                 # agrégation, macros, parsing
ruff check src tests   # lint
mypy src               # typage strict
```

---

## Légal

Lit uniquement les fichiers de log écrits publiquement par le jeu dans le
dossier Saved Games. Aucune injection, aucun hook mémoire, aucune modification
du jeu. Non affilié à Frontier Developments.
