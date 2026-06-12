/**
 * Store principal — état du jeu Elite Dangerous.
 *
 * Pinia est la solution officielle de gestion d'état pour Vue 3.
 * Ce store est la source de vérité unique pour toutes les données
 * du jeu reçues via WebSocket.
 *
 * Structure d'un store Pinia :
 *   state   → les données brutes (équivalent data() dans Vue)
 *   getters → propriétés calculées (équivalent computed dans Vue)
 *   actions → méthodes qui modifient l'état (plus de mutations comme Vuex)
 *
 * N'importe quel composant accède à ce store via :
 *   const game = useGameStore()
 *   game.ship.hull_health  // accès direct, pas de prop drilling
 */

import { defineStore } from 'pinia'
import type { GameState, Macro } from '@/types'

// ── État initial ──────────────────────────────────────────────────

function emptyState(): GameState {
  return {
    connected: false,
    commander: { name: '', credits: 0, game_mode: '' },
    ship: {
      type: '', type_label: '', name: '', ident: '',
      hull_health: 100, fuel_main: 0, fuel_cap: 0,
      cargo: 0, cargo_cap: 0, rebuy: 0,
    },
    status: {
      docked: false, landed: false, landing_gear: false, shields: true,
      supercruise: false, flight_assist_off: false, hardpoints: false,
      cargo_scoop: false, lights: false, silent_running: false,
      fsd_charging: false, fsd_cooldown: false, fsd_masslock: false,
      low_fuel: false, overheating: false, in_danger: false,
      being_interdicted: false, analysis_mode: false, night_vision: false,
      sco_active: false, on_foot: false,
      pips: [2, 2, 2], fire_group: 0, gui_focus: 0, legal_state: 'Clean',
    },
    navigation: {
      system: '', body: '', station: '', station_type: '',
      latitude: null, longitude: null, altitude: null, heading: null,
      route: [], jumps_remaining: 0,
    },
    combat: {
      shields_up: true, under_attack: false, interdicted: false,
      target: {
        locked: false, ship: '', pilot: '', rank: '',
        shield_health: 0, hull_health: 0,
        faction: '', legal_status: '', bounty: 0, scan_stage: 0,
      },
      last_bounty_total: 0, last_bounty_target: '',
      last_bounty_victim_faction: '', last_bounty_rewards: [],
      kills_session: 0, bonds_session: 0, bonds_total_session: 0,
    },
    cargo: [],
    enrichment: {},
    last_event: '',
    timestamp: '',
  }
}

// ── Store ─────────────────────────────────────────────────────────

export const useGameStore = defineStore('game', {

  // ── State ───────────────────────────────────────────────────────
  // Données brutes. Déclarées ici pour que Pinia les rende réactives.
  state: () => ({
    ...emptyState(),
    macros: [] as Macro[],
  }),

  // ── Getters ─────────────────────────────────────────────────────
  // Propriétés calculées depuis l'état. Mises en cache automatiquement.
  // Recalculées seulement si leurs dépendances changent.
  getters: {
    hullPercent: (state): number => state.ship.hull_health ?? 100,

    hullClass: (state): string => {
      const h = state.ship.hull_health ?? 100
      return h < 30 ? 'warn' : h < 60 ? '' : 'ok'
    },

    fuelText: (state): string => {
      const fm = state.ship.fuel_main ?? 0
      const fc = state.ship.fuel_cap || 0
      return fc
        ? `${fm.toFixed(1)} / ${fc.toFixed(0)} T`
        : `${fm.toFixed(1)} T`
    },

    fuelPercent: (state): number => {
      const fm = state.ship.fuel_main ?? 0
      const fc = state.ship.fuel_cap || 0
      return fc ? Math.min(100, (fm / fc) * 100) : 0
    },

    pips: (state): [number, number, number] =>
      state.status.pips ?? [2, 2, 2],

    macrosById: (state): Record<string, Macro> =>
      Object.fromEntries(state.macros.map(m => [m.id, m])),

    isInDanger: (state): boolean =>
      state.combat.under_attack ||
      state.status.in_danger ||
      state.combat.interdicted,
  },

  // ── Actions ─────────────────────────────────────────────────────
  // Méthodes qui modifient l'état. Peuvent être async.
  // Pas de mutations séparées comme dans Vuex — on modifie this directement.
  actions: {
    applySnapshot(data: GameState): void {
      // Remplace tout l'état d'un coup (connexion initiale)
      Object.assign(this, data)
    },

    applyPatch(changes: Record<string, unknown>): void {
      // Applique un diff partiel (notation pointée : "ship.hull_health")
      for (const [path, value] of Object.entries(changes)) {
        const keys = path.split('.')
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        let node: any = this
        for (let i = 0; i < keys.length - 1; i++) {
          if (!(keys[i] in node)) node[keys[i]] = {}
          node = node[keys[i]]
        }
        node[keys[keys.length - 1]] = value
      }
    },

    setMacros(macros: Macro[]): void {
      this.macros = macros
    },

    updateMacroKey(macroId: string, keyspec: Macro['key']): void {
      const macro = this.macros.find(m => m.id === macroId)
      if (macro) macro.key = keyspec
    },
  },
})
