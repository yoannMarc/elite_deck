<template>
  <div class="grid">

    <!-- Vaisseau -->
    <section class="panel">
      <h2>Vaisseau</h2>
      <div class="row">
        <span class="k">Type</span>
        <span class="v">{{ game.ship.type_label || game.ship.type || '—' }}</span>
      </div>
      <div class="row">
        <span class="k">Nom</span>
        <span class="v">{{ game.ship.name || '—' }}</span>
      </div>
      <div class="row">
        <span class="k">Coque</span>
        <span class="v" :class="game.hullClass">{{ game.hullPercent.toFixed(1) }} %</span>
      </div>
      <div class="bar hull">
        <span :style="{ width: game.hullPercent + '%' }"></span>
      </div>
      <div class="row" style="margin-top:8px">
        <span class="k">Carburant</span>
        <span class="v">{{ game.fuelText }}</span>
      </div>
      <div class="bar fuel">
        <span :style="{ width: game.fuelPercent + '%' }"></span>
      </div>
      <div class="row" style="margin-top:8px">
        <span class="k">Cargo</span>
        <span class="v">
          {{ game.ship.cargo || 0 }}
          {{ game.ship.cargo_cap ? ` / ${game.ship.cargo_cap} T` : ' T' }}
        </span>
      </div>
    </section>

    <!-- Énergie -->
    <section class="panel">
      <h2>Distribution énergie</h2>
      <div class="pips">
        <PipBar label="SYS" group="sys" :value="game.pips[0]" />
        <PipBar label="ENG" group="eng" :value="game.pips[1]" />
        <PipBar label="WEP" group="wep" :value="game.pips[2]" />
      </div>
    </section>

    <!-- Navigation -->
    <section class="panel">
      <h2>Navigation</h2>
      <div class="row">
        <span class="k">Système</span>
        <span class="v">{{ game.navigation.system || '—' }}</span>
      </div>
      <div class="row">
        <span class="k">Corps</span>
        <span class="v">{{ game.navigation.body || '—' }}</span>
      </div>
      <div class="row">
        <span class="k">Station</span>
        <span class="v">{{ game.navigation.station || '—' }}</span>
      </div>
      <div class="row">
        <span class="k">Sauts restants</span>
        <span class="v big">{{ game.navigation.jumps_remaining ?? 0 }}</span>
      </div>
    </section>

    <!-- Route -->
    <section class="panel">
      <h2>Route planifiée</h2>
      <ul class="route" v-if="game.navigation.route.length">
        <li v-for="sys in game.navigation.route" :key="sys">{{ sys }}</li>
      </ul>
      <p class="empty" v-else>Aucune route tracée</p>
    </section>

    <!-- Flags -->
    <section class="panel col-full">
      <h2>État des systèmes</h2>
      <div class="flags">
        <div
          v-for="f in FLAG_DEFS"
          :key="f.key"
          class="chip"
          :class="{
            on: (game.status as Record<string, unknown>)[f.key],
            warn: f.warn
          }"
        >{{ f.label }}</div>
      </div>
    </section>

  </div>
</template>

<script setup lang="ts">
import { useGameStore } from '@/stores/game'
import PipBar from '@/components/PipBar.vue'

const game = useGameStore()

const FLAG_DEFS = [
  { key: 'landing_gear',      label: 'Train' },
  { key: 'shields',           label: 'Boucliers' },
  { key: 'hardpoints',        label: 'Armes' },
  { key: 'cargo_scoop',       label: 'Cargo scoop' },
  { key: 'analysis_mode',     label: 'Analyse' },
  { key: 'supercruise',       label: 'Supercruise' },
  { key: 'lights',            label: 'Lumières' },
  { key: 'fsd_charging',      label: 'FSD' },
  { key: 'docked',            label: 'Amarré' },
  { key: 'silent_running',    label: 'Silent' },
  { key: 'night_vision',      label: 'Vision nuit' },
  { key: 'sco_active',        label: 'SCO' },
  { key: 'low_fuel',          label: 'Carb. bas',    warn: true },
  { key: 'overheating',       label: 'Surchauffe',   warn: true },
  { key: 'in_danger',         label: 'Danger',       warn: true },
  { key: 'being_interdicted', label: 'Interdiction', warn: true },
] as const
</script>
