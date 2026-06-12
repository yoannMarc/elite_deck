// Types miroir des modèles Python (core/models.py)
// Maintenus en parallèle — si tu modifies GameState côté Python,
// mets à jour ces types.

export interface Commander {
  name: string
  credits: number
  game_mode: string
}

export interface Ship {
  type: string
  type_label: string
  name: string
  ident: string
  hull_health: number
  fuel_main: number
  fuel_cap: number
  cargo: number
  cargo_cap: number
  rebuy: number
}

export interface Status {
  docked: boolean
  landed: boolean
  landing_gear: boolean
  shields: boolean
  supercruise: boolean
  flight_assist_off: boolean
  hardpoints: boolean
  cargo_scoop: boolean
  lights: boolean
  silent_running: boolean
  fsd_charging: boolean
  fsd_cooldown: boolean
  fsd_masslock: boolean
  low_fuel: boolean
  overheating: boolean
  in_danger: boolean
  being_interdicted: boolean
  analysis_mode: boolean
  night_vision: boolean
  sco_active: boolean
  on_foot: boolean
  pips: [number, number, number]
  fire_group: number
  gui_focus: number
  legal_state: string
}

export interface Navigation {
  system: string
  body: string
  station: string
  station_type: string
  latitude: number | null
  longitude: number | null
  altitude: number | null
  heading: number | null
  route: string[]
  jumps_remaining: number
}

export interface CombatTarget {
  locked: boolean
  ship: string
  pilot: string
  rank: string
  shield_health: number
  hull_health: number
  faction: string
  legal_status: string
  bounty: number
  scan_stage: number
}

export interface BountyReward {
  faction: string
  reward: number
}

export interface Combat {
  shields_up: boolean
  under_attack: boolean
  interdicted: boolean
  target: CombatTarget
  last_bounty_total: number
  last_bounty_target: string
  last_bounty_victim_faction: string
  last_bounty_rewards: BountyReward[]
  kills_session: number
  bonds_session: number
  bonds_total_session: number
}

export interface CargoItem {
  name: string
  count: number
}

export interface GameState {
  connected: boolean
  commander: Commander
  ship: Ship
  status: Status
  navigation: Navigation
  combat: Combat
  cargo: CargoItem[]
  enrichment: Record<string, unknown>
  last_event: string
  timestamp: string
}

// ── Macros ─────────────────────────────────────────────────────────

export interface KeySpec {
  char: string | null
  name: string | null
  vk: number | null
  scan: number | null
  modifiers: string[]
  label: string
}

export interface Macro {
  id: string
  label: string
  kind: 'tap' | 'sequence'
  status_flag: string
  category: string
  accent: string
  key: KeySpec
  sequence: KeySpec[]
}
