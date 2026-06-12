"""Store d'état — agrège le flux de fichiers du jeu en un ``GameState``.

Émet des *diffs* incrémentaux (notation pointée) aux abonnés via des queues
asyncio, pour minimiser la bande passante des clients distants (tablette).
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from back.core.flags import FLAGS, FLAGS2, decode_flags
from back.core.models import BountyReward, CargoItem, CombatState, CombatTarget, GameState


def diff_dict(old: dict[str, Any], new: dict[str, Any], path: str = "") -> dict[str, Any]:
    """Diff récursif → chemins modifiés en notation pointée."""
    changes: dict[str, Any] = {}
    for key, new_val in new.items():
        full = f"{path}.{key}" if path else key
        old_val = old.get(key)
        if isinstance(new_val, dict) and isinstance(old_val, dict):
            changes.update(diff_dict(old_val, new_val, full))
        elif new_val != old_val:
            changes[full] = new_val
    return changes


# Handler : mute le GameState en place
EventHandler = Callable[[GameState, dict[str, Any]], None]


class StateStore:
    """Détient le ``GameState`` et notifie les abonnés à chaque changement."""

    def __init__(self) -> None:
        self._state = GameState()
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()
        self._lock = asyncio.Lock()

    # ── Souscription ──────────────────────────────────────────────────

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        self._subscribers.discard(queue)

    @property
    def snapshot(self) -> dict[str, Any]:
        return self._state.to_dict()

    @property
    def state(self) -> GameState:
        return self._state

    # ── Mutations ─────────────────────────────────────────────────────

    async def apply_status(self, data: dict[str, Any]) -> None:
        async with self._lock:
            old = self._state.to_dict()
            st = self._state.status
            flags = decode_flags(data.get("Flags", 0), FLAGS)
            flags2 = decode_flags(data.get("Flags2", 0), FLAGS2)

            for key in (
                "docked", "landed", "landing_gear", "shields", "supercruise",
                "flight_assist_off", "hardpoints", "cargo_scoop", "lights",
                "silent_running", "fsd_charging", "fsd_cooldown", "fsd_masslock",
                "low_fuel", "overheating", "in_danger", "being_interdicted",
                "analysis_mode", "night_vision",
            ):
                setattr(st, key, flags[key])
            st.sco_active = flags2["sco_active"]
            st.on_foot = flags2["on_foot"]

            st.pips = data.get("Pips", [2, 2, 2])
            st.fire_group = data.get("FireGroup", 0)
            st.gui_focus = data.get("GuiFocus", 0)
            st.legal_state = data.get("LegalState", "Clean")

            fuel = data.get("Fuel", {})
            if fuel:
                self._state.ship.fuel_main = fuel.get("FuelMain", 0.0)
            self._state.ship.cargo = data.get("Cargo", self._state.ship.cargo)

            nav = self._state.navigation
            if "Latitude" in data:
                nav.latitude = data.get("Latitude")
                nav.longitude = data.get("Longitude")
                nav.altitude = data.get("Altitude")
                nav.heading = data.get("Heading")

            self._state.connected = True
            self._state.timestamp = data.get("timestamp", "")
            self._state.last_event = "Status"
            await self._notify(old)

    async def apply_event(self, event: dict[str, Any]) -> None:
        handler = _HANDLERS.get(event.get("event", ""))
        if handler is None:
            return
        async with self._lock:
            old = self._state.to_dict()
            handler(self._state, event)
            self._state.timestamp = event.get("timestamp", "")
            self._state.last_event = event.get("event", "")
            await self._notify(old)

    async def apply_cargo(self, data: dict[str, Any]) -> None:
        async with self._lock:
            old = self._state.to_dict()
            inv = data.get("Inventory", [])
            self._state.cargo = [
                CargoItem(name=i.get("Name", ""), count=i.get("Count", 0)) for i in inv
            ]
            self._state.ship.cargo = data.get(
                "Count", sum(c.count for c in self._state.cargo)
            )
            await self._notify(old)

    async def apply_navroute(self, data: dict[str, Any]) -> None:
        async with self._lock:
            old = self._state.to_dict()
            route = data.get("Route", [])
            self._state.navigation.route = [r.get("StarSystem", "") for r in route]
            self._state.navigation.jumps_remaining = max(
                0, len(self._state.navigation.route) - 1
            )
            await self._notify(old)

    async def apply_enrichment(self, provider: str, payload: dict[str, Any]) -> None:
        """Point d'entrée pour les intégrations externes (EDSM, FDevIDs…)."""
        async with self._lock:
            old = self._state.to_dict()
            self._state.enrichment[provider] = payload
            await self._notify(old)

    # ── Notification ──────────────────────────────────────────────────

    async def _notify(self, old: dict[str, Any]) -> None:
        new = self._state.to_dict()
        changes = diff_dict(old, new)
        if not changes:
            return
        payload = {"type": "patch", "changes": changes, "ts": new["timestamp"]}
        dead: list[asyncio.Queue[dict[str, Any]]] = []
        for queue in self._subscribers:
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                dead.append(queue)
        for queue in dead:
            self._subscribers.discard(queue)


# ── Handlers d'événements Journal ─────────────────────────────────────────────


def _h_load_game(s: GameState, e: dict[str, Any]) -> None:
    s.commander.name = e.get("Commander", s.commander.name)
    s.commander.credits = e.get("Credits", s.commander.credits)
    s.commander.game_mode = e.get("GameMode", s.commander.game_mode)
    s.ship.type = e.get("Ship", s.ship.type)
    s.ship.name = e.get("ShipName", s.ship.name)
    s.ship.ident = e.get("ShipIdent", s.ship.ident)
    s.ship.fuel_cap = e.get("FuelCapacity", s.ship.fuel_cap)
    s.connected = True


def _h_loadout(s: GameState, e: dict[str, Any]) -> None:
    s.ship.type = e.get("Ship", s.ship.type)
    s.ship.name = e.get("ShipName", s.ship.name)
    s.ship.ident = e.get("ShipIdent", s.ship.ident)
    s.ship.hull_health = e.get("HullHealth", 1.0) * 100.0
    s.ship.cargo_cap = e.get("CargoCapacity", s.ship.cargo_cap)
    s.ship.rebuy = e.get("Rebuy", s.ship.rebuy)
    fc = e.get("FuelCapacity", {})
    if isinstance(fc, dict):
        s.ship.fuel_cap = fc.get("Main", s.ship.fuel_cap)


def _h_fsd_jump(s: GameState, e: dict[str, Any]) -> None:
    arrived = e.get("StarSystem", s.navigation.system)
    s.navigation.system = arrived
    s.navigation.body = e.get("Body", "")
    s.navigation.station = ""
    if arrived in s.navigation.route:
        idx = s.navigation.route.index(arrived)
        s.navigation.route = s.navigation.route[idx + 1 :]
    s.navigation.jumps_remaining = len(s.navigation.route)


def _h_location(s: GameState, e: dict[str, Any]) -> None:
    s.navigation.system = e.get("StarSystem", s.navigation.system)
    s.navigation.body = e.get("Body", s.navigation.body)
    s.navigation.station = e.get("StationName", "")
    s.navigation.station_type = e.get("StationType", "")


def _h_docked(s: GameState, e: dict[str, Any]) -> None:
    s.navigation.station = e.get("StationName", "")
    s.navigation.station_type = e.get("StationType", "")
    s.navigation.system = e.get("StarSystem", s.navigation.system)


def _h_undocked(s: GameState, e: dict[str, Any]) -> None:
    s.navigation.station = ""
    s.navigation.station_type = ""


def _h_supercruise_exit(s: GameState, e: dict[str, Any]) -> None:
    s.navigation.body = e.get("Body", s.navigation.body)


def _h_hull_damage(s: GameState, e: dict[str, Any]) -> None:
    s.ship.hull_health = e.get("Health", 1.0) * 100.0


def _h_shipyard_swap(s: GameState, e: dict[str, Any]) -> None:
    s.ship.type = e.get("ShipType", s.ship.type)


# ── Handlers combat ───────────────────────────────────────────────────────────


def _h_shield_state(s: GameState, e: dict[str, Any]) -> None:
    s.combat.shields_up = bool(e.get("ShieldsUp", True))
    # Synchronise aussi le Status (source de vérité pour l'UI flags)
    s.status.shields = s.combat.shields_up


def _h_under_attack(s: GameState, e: dict[str, Any]) -> None:
    s.combat.under_attack = True
    # under_attack est un signal ponctuel — il sera remis à False au prochain
    # événement neutre (ex. ShieldState, FSDJump). Pas de timer asyncio ici
    # pour rester dans la contrainte "handler pur, pas d'effets de bord".


def _h_ship_targeted(s: GameState, e: dict[str, Any]) -> None:
    t = s.combat.target
    if not e.get("TargetLocked", False):
        s.combat.target = CombatTarget()
        return

    t.locked = True
    t.ship = e.get("Ship", t.ship)
    t.scan_stage = e.get("ScanStage", t.scan_stage)

    if t.scan_stage >= 1:
        t.pilot = e.get("PilotName", t.pilot)
        t.rank = e.get("PilotRank", t.rank)

    if t.scan_stage >= 2:
        t.shield_health = e.get("ShieldHealth", t.shield_health)
        t.hull_health = e.get("HullHealth", t.hull_health)

    if t.scan_stage >= 3:
        t.faction = e.get("Faction", t.faction)
        t.legal_status = e.get("LegalStatus", t.legal_status)
        t.bounty = e.get("Bounty", t.bounty)


def _h_bounty(s: GameState, e: dict[str, Any]) -> None:
    s.combat.last_bounty_total = e.get("TotalReward", e.get("Reward", 0))
    s.combat.last_bounty_target = e.get("Target", "")
    s.combat.last_bounty_victim_faction = e.get("VictimFaction", "")

    rewards_raw = e.get("Rewards")
    if rewards_raw:
        s.combat.last_bounty_rewards = [
            BountyReward(faction=r.get("Faction", ""), reward=r.get("Reward", 0))
            for r in rewards_raw
        ]
    else:
        s.combat.last_bounty_rewards = [
            BountyReward(faction=e.get("Faction", ""), reward=e.get("Reward", 0))
        ]

    s.combat.kills_session += 1
    s.combat.under_attack = False


def _h_faction_kill_bond(s: GameState, e: dict[str, Any]) -> None:
    s.combat.bonds_session += 1
    s.combat.bonds_total_session += e.get("Reward", 0)
    s.combat.under_attack = False


def _h_interdicted(s: GameState, e: dict[str, Any]) -> None:
    # Submitted=True → le joueur a cédé → plus sous interdiction active
    s.combat.interdicted = not e.get("Submitted", False)
    s.status.being_interdicted = s.combat.interdicted


def _h_escape_interdiction(s: GameState, e: dict[str, Any]) -> None:
    s.combat.interdicted = False
    s.status.being_interdicted = False


def _h_pvp_kill(s: GameState, e: dict[str, Any]) -> None:
    s.combat.kills_session += 1
    s.combat.under_attack = False


def _h_died(s: GameState, e: dict[str, Any]) -> None:
    # Reset de l'état de combat à la mort, en conservant les stats de session
    kills = s.combat.kills_session
    bonds = s.combat.bonds_session
    bonds_total = s.combat.bonds_total_session
    s.combat = CombatState(
        kills_session=kills,
        bonds_session=bonds,
        bonds_total_session=bonds_total,
    )
    s.ship.hull_health = 0.0


_HANDLERS: dict[str, EventHandler] = {
    # Navigation / vaisseau
    "LoadGame": _h_load_game,
    "Loadout": _h_loadout,
    "FSDJump": _h_fsd_jump,
    "CarrierJump": _h_fsd_jump,
    "Location": _h_location,
    "Docked": _h_docked,
    "Undocked": _h_undocked,
    "SupercruiseExit": _h_supercruise_exit,
    "HullDamage": _h_hull_damage,
    "ShipyardSwap": _h_shipyard_swap,
    # Combat
    "ShieldState": _h_shield_state,
    "UnderAttack": _h_under_attack,
    "ShipTargeted": _h_ship_targeted,
    "Bounty": _h_bounty,
    "FactionKillBond": _h_faction_kill_bond,
    "Interdicted": _h_interdicted,
    "EscapeInterdiction": _h_escape_interdiction,
    "PVPKill": _h_pvp_kill,
    "Died": _h_died,
}