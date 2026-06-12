<template>
  <div class="wrap">
    <!-- ── Header ─────────────────────────────────────────────── -->
    <header class="ed-header">
      <h1>◈ Elite Deck</h1>
      <div class="conn" :class="{ live: game.connected }">
        <span class="dot"></span>
        <span>{{ game.connected ? 'En direct' : 'Reconnexion…' }}</span>
      </div>
    </header>

    <!-- ── Tabs ───────────────────────────────────────────────── -->
    <nav class="tabs">
      <RouterLink
        v-for="tab in tabs"
        :key="tab.name"
        :to="{ name: tab.name }"
        class="tab"
        active-class="active"
      >
        {{ tab.label }}
      </RouterLink>
    </nav>

    <!-- ── Vue courante ───────────────────────────────────────── -->
    <RouterView v-slot="{ Component }">
      <Transition name="tab" mode="out-in">
        <component :is="Component" :send="send" :ack-hint="ackHint" />
      </Transition>
    </RouterView>

    <footer>Temps réel · WebSocket · Les commandes sont exécutées sur le PC</footer>
  </div>
</template>

<script setup lang="ts">
import { useGameStore } from '@/stores/game'
import { useWebSocket } from '@/composables/useWebSocket'

const game = useGameStore()
const { send, ackHint } = useWebSocket()

const tabs = [
  { name: 'deck',      label: '◈ Commandes' },
  { name: 'telemetry', label: '⊙ Télémétrie' },
  { name: 'combat',    label: '⚔ Combat' },
]
</script>
