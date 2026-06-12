# Elite Deck — Frontend Vue 3

Interface tablette avec Vite + Vue 3 + Pinia + Vue Router.

## Prérequis

- Node.js >= 20 (https://nodejs.org)
- Le backend Python doit tourner sur le port 3300

## Installation

```bash
cd elite_deck_frontend
npm install
```

## Développement

```bash
# 1. Lancer le backend Python
cd ../elite_deck
python -m elite_deck --host 0.0.0.0

# 2. Dans un autre terminal, lancer Vite
cd elite_deck_frontend
npm run dev
# → http://localhost:5173
```

Vite proxie automatiquement `/ws` et `/api` vers Python (port 3300).
Le Hot Module Replacement rechargea l'interface sans perdre la connexion WS.

## Production

```bash
npm run build
# Génère les fichiers dans ../elite_deck/src/elite_deck/web/
# Servis directement par aiohttp
```

Après le build, lancer seulement Python :
```bash
python -m elite_deck --host 0.0.0.0
# → http://localhost:3300 (interface + API + WebSocket)
```

## Structure

```
src/
├── main.ts                    ← bootstrap Vue + Pinia + Router
├── App.vue                    ← header + tabs + router-view
├── types.ts                   ← types TypeScript (miroir des models Python)
├── stores/
│   └── game.ts                ← store Pinia (état unique du jeu)
├── composables/
│   └── useWebSocket.ts        ← connexion WS, alimente le store
├── views/                     ← une vue = un onglet
│   ├── DeckView.vue
│   ├── TelemetryView.vue
│   └── CombatView.vue
└── components/                ← composants réutilisables
    ├── MacroButton.vue
    ├── PipBar.vue
    └── KeybindModal.vue
```

## Ajouter un onglet

1. Créer `src/views/ExplorationView.vue`
2. Ajouter la route dans `main.ts`
3. Ajouter le tab dans `App.vue`

C'est tout — Pinia fournit les données, le composant les affiche.
