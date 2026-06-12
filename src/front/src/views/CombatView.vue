<template>
  <div class="grid">

    <!-- État combat -->
    <section class="panel">
      <h2>État</h2>
      <div class="row">
        <span class="k">Boucliers</span>
        <span class="v" :class="game.combat.shields_up ? 'ok' : 'warn'">
          {{ game.combat.shields_up ? '● Actifs' : '○ Hors ligne' }}
        </span>
      </div>
      <div class="row">
        <span class="k">Attaque</span>
        <span class="v" :class="{ warn: game.combat.under_attack }">
          {{ game.combat.under_attack ? '⚠ Sous le feu' : '— Calme' }}
        </span>
      </div>
      <div class="row">
        <span class="k">Interdiction</span>
        <span class="v" :class="{ warn: game.combat.interdicted }">
          {{ game.combat.interdicted ? '⚠ En cours' : '—' }}
        </span>
      </div>
    </section>

    <!-- Stats de session -->
    <section class="panel">
      <h2>Session</h2>
      <div class="row">
        <span class="k">Éliminations</span>
        <span class="v big">{{ game.combat.kills_session }}</span>
      </div>
      <div class="row">
        <span class="k">Bonds combat</span>
        <span class="v">{{ game.combat.bonds_session }}</span>
      </div>
      <div class="row">
        <span class="k">Total bonds</span>
        <span class="v">{{ fmtCredits(game.combat.bonds_total_session) }}</span>
      </div>
    </section>

    <!-- Cible active -->
    <section class="panel col-full" v-if="game.combat.target.locked">
      <h2>Cible</h2>
      <div class="row">
        <span class="k">Vaisseau</span>
        <span class="v">{{ game.combat.target.ship || '—' }}</span>
      </div>
      <template v-if="game.combat.target.scan_stage >= 1">
        <div class="row">
          <span class="k">Pilote</span>
          <span class="v">{{ game.combat.target.pilot }}</span>
        </div>
        <div class="row">
          <span class="k">Rang</span>
          <span class="v">{{ game.combat.target.rank }}</span>
        </div>
      </template>
      <template v-if="game.combat.target.scan_stage >= 2">
        <div class="row">
          <span class="k">Boucliers</span>
          <span class="v">{{ pct(game.combat.target.shield_health) }}</span>
        </div>
        <div class="row">
          <span class="k">Coque</span>
          <span class="v">{{ pct(game.combat.target.hull_health) }}</span>
        </div>
      </template>
      <template v-if="game.combat.target.scan_stage >= 3">
        <div class="row">
          <span class="k">Faction</span>
          <span class="v">{{ game.combat.target.faction }}</span>
        </div>
        <div class="row" v-if="game.combat.target.bounty">
          <span class="k">Prime</span>
          <span class="v warn">{{ fmtCredits(game.combat.target.bounty) }}</span>
        </div>
      </template>
    </section>

    <!-- Dernière prime -->
    <section class="panel col-full" v-if="game.combat.last_bounty_target">
      <h2>Dernière prime</h2>
      <div class="row">
        <span class="k">Cible</span>
        <span class="v">{{ game.combat.last_bounty_target }}</span>
      </div>
      <div class="row">
        <span class="k">Faction victime</span>
        <span class="v">{{ game.combat.last_bounty_victim_faction }}</span>
      </div>
      <div class="row">
        <span class="k">Total</span>
        <span class="v ok">{{ fmtCredits(game.combat.last_bounty_total) }}</span>
      </div>
    </section>

  </div>
</template>

<script setup lang="ts">
import { useGameStore } from '@/stores/game'

const game = useGameStore()

function fmtCredits(n: number): string {
  return (n || 0).toLocaleString('fr-FR') + ' Cr'
}

function pct(v: number): string {
  return (v * 100).toFixed(0) + ' %'
}
</script>
