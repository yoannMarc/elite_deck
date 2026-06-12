"""Tests des handlers de combat."""

from __future__ import annotations

from back.core.store import StateStore


async def test_shield_state_down_and_up() -> None:
    store = StateStore()
    await store.apply_event({"event": "ShieldState", "ShieldsUp": False, "timestamp": "t"})
    assert not store.state.combat.shields_up 
    assert not store.state.status.shields 

    await store.apply_event({"event": "ShieldState", "ShieldsUp": True, "timestamp": "t"})
    shields_up: bool = store.state.combat.shields_up
    shields: bool = store.state.status.shields
    assert shields_up
    assert shields

async def test_under_attack() -> None:
    store = StateStore()
    await store.apply_event({"event": "UnderAttack", "Target": "You", "timestamp": "t"})
    assert store.state.combat.under_attack is True


async def test_ship_targeted_scan_stage_0() -> None:
    store = StateStore()
    await store.apply_event({
        "event": "ShipTargeted", "TargetLocked": True,
        "Ship": "viper", "ScanStage": 0, "timestamp": "t",
    })
    assert store.state.combat.target.locked is True
    assert store.state.combat.target.ship == "viper"
    assert store.state.combat.target.pilot == ""  # pas encore scanné


async def test_ship_targeted_full_scan() -> None:
    store = StateStore()
    await store.apply_event({
        "event": "ShipTargeted", "TargetLocked": True,
        "Ship": "python", "ScanStage": 3,
        "PilotName": "Cmdr Foo", "PilotRank": "Elite",
        "ShieldHealth": 0.85, "HullHealth": 0.92,
        "Faction": "Pilots Federation", "LegalStatus": "Clean", "Bounty": 0,
        "timestamp": "t",
    })
    t = store.state.combat.target
    assert t.pilot == "Cmdr Foo"
    assert t.rank == "Elite"
    assert t.shield_health == 0.85
    assert t.faction == "Pilots Federation"


async def test_ship_targeted_lost() -> None:
    store = StateStore()
    await store.apply_event({
        "event": "ShipTargeted", "TargetLocked": True,
        "Ship": "viper", "ScanStage": 0, "timestamp": "t",
    })
    await store.apply_event({"event": "ShipTargeted", "TargetLocked": False, "timestamp": "t"})
    assert store.state.combat.target.locked is False
    assert store.state.combat.target.ship == ""


async def test_bounty_ship() -> None:
    store = StateStore()
    await store.apply_event({
        "event": "Bounty",
        "Rewards": [{"Faction": "Nehet Patron's Principles", "Reward": 5620}],
        "Target": "empire_eagle",
        "TotalReward": 5620,
        "VictimFaction": "Nehet Progressive Party",
        "timestamp": "t",
    })
    c = store.state.combat
    assert c.last_bounty_total == 5620
    assert c.last_bounty_target == "empire_eagle"
    assert c.kills_session == 1
    assert c.last_bounty_rewards[0].faction == "Nehet Patron's Principles"
    assert c.under_attack is False


async def test_bounty_skimmer() -> None:
    store = StateStore()
    await store.apply_event({
        "event": "Bounty",
        "Faction": "HIP 18828 Empire Consulate",
        "Target": "Skimmer",
        "Reward": 1000,
        "VictimFaction": "HIP 18828 Empire Consulate",
        "timestamp": "t",
    })
    assert store.state.combat.kills_session == 1
    assert store.state.combat.last_bounty_rewards[0].reward == 1000


async def test_faction_kill_bond() -> None:
    store = StateStore()
    await store.apply_event({
        "event": "FactionKillBond", "Reward": 500,
        "AwardingFaction": "Jarildekald Public Industry",
        "VictimFaction": "Lencali Freedom Party",
        "timestamp": "t",
    })
    assert store.state.combat.bonds_session == 1
    assert store.state.combat.bonds_total_session == 500


async def test_interdicted_submitted() -> None:
    store = StateStore()
    await store.apply_event({
        "event": "Interdicted", "Submitted": True,
        "Interdictor": "Dread Pirate", "IsPlayer": False,
        "timestamp": "t",
    })
    assert store.state.combat.interdicted is False
    assert store.state.status.being_interdicted is False


async def test_interdicted_not_submitted() -> None:
    store = StateStore()
    await store.apply_event({
        "event": "Interdicted", "Submitted": False,
        "Interdictor": "Dread Pirate", "IsPlayer": False,
        "timestamp": "t",
    })
    assert store.state.combat.interdicted is True
    assert store.state.status.being_interdicted is True


async def test_escape_interdiction() -> None:
    store = StateStore()
    await store.apply_event({
        "event": "Interdicted", "Submitted": False, "Interdictor": "X", "timestamp": "t",
    })
    await store.apply_event({"event": "EscapeInterdiction", "Interdictor": "X", "timestamp": "t"})
    assert store.state.combat.interdicted is False


async def test_pvp_kill() -> None:
    store = StateStore()
    await store.apply_event({
        "event": "PVPKill", "Victim": "Cmdr X", "CombatRank": 3, "timestamp": "t",
    })
    assert store.state.combat.kills_session == 1


async def test_died_resets_combat_keeps_stats() -> None:
    store = StateStore()
    # Accumule des kills
    await store.apply_event({
        "event": "Bounty", "Rewards": [{"Faction": "F", "Reward": 1000}],
        "Target": "viper", "TotalReward": 1000, "VictimFaction": "F", "timestamp": "t",
    })
    await store.apply_event({"event": "PVPKill", "Victim": "X", "CombatRank": 2, "timestamp": "t"})
    assert store.state.combat.kills_session == 2

    await store.apply_event({
        "event": "Died", "KillerName": "NPC", "KillerShip": "viper", "timestamp": "t",
    })

    # Stats de session conservées
    assert store.state.combat.kills_session == 2
    # État de combat remis à zéro
    assert store.state.combat.shields_up is True
    assert store.state.combat.under_attack is False
    assert store.state.ship.hull_health == 0.0


async def test_combat_patch_diffused() -> None:
    """Vérifie que les changements de combat génèrent bien des diffs WS."""
    store = StateStore()
    queue = store.subscribe()
    await store.apply_event({
        "event": "Bounty", "Rewards": [{"Faction": "F", "Reward": 500}],
        "Target": "eagle", "TotalReward": 500, "VictimFaction": "F", "timestamp": "t",
    })
    patch = await queue.get()
    assert patch["type"] == "patch"
    assert "combat.kills_session" in patch["changes"]
    assert patch["changes"]["combat.kills_session"] == 1