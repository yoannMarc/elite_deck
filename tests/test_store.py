"""Tests de l'agrégation d'état."""

from __future__ import annotations

import pytest

from elite_deck.core.store import StateStore, diff_dict


async def test_load_game_and_loadout() -> None:
    store = StateStore()
    await store.apply_event({
        "event": "LoadGame", "Commander": "Test", "Credits": 1000,
        "Ship": "asp", "ShipName": "Boat", "timestamp": "t",
    })
    await store.apply_event({
        "event": "Loadout", "Ship": "asp", "HullHealth": 0.9,
        "CargoCapacity": 64, "FuelCapacity": {"Main": 32.0}, "timestamp": "t",
    })
    s = store.snapshot
    assert s["commander"]["name"] == "Test"
    assert s["commander"]["credits"] == 1000
    assert s["ship"]["cargo_cap"] == 64
    assert s["ship"]["hull_health"] == pytest.approx(90.0)
    assert s["ship"]["fuel_cap"] == 32.0


async def test_status_flags_decoded() -> None:
    store = StateStore()
    flags = (1 << 2) | (1 << 3) | (1 << 8)  # gear + shields + lights
    await store.apply_status({
        "event": "Status", "Flags": flags, "Pips": [4, 2, 2],
        "Fuel": {"FuelMain": 12.0}, "timestamp": "t",
    })
    s = store.snapshot
    assert s["status"]["landing_gear"] is True
    assert s["status"]["shields"] is True
    assert s["status"]["lights"] is True
    assert s["status"]["hardpoints"] is False
    assert s["status"]["pips"] == [4, 2, 2]


async def test_route_progression() -> None:
    store = StateStore()
    await store.apply_navroute({"Route": [
        {"StarSystem": "Sol"}, {"StarSystem": "Wolf 359"}, {"StarSystem": "Sirius"},
    ]})
    await store.apply_event({"event": "FSDJump", "StarSystem": "Wolf 359", "timestamp": "t"})
    s = store.snapshot
    assert s["navigation"]["system"] == "Wolf 359"
    assert s["navigation"]["route"] == ["Sirius"]
    assert s["navigation"]["jumps_remaining"] == 1


async def test_diffs_emitted() -> None:
    store = StateStore()
    queue = store.subscribe()
    await store.apply_event({"event": "LoadGame", "Commander": "X", "timestamp": "t"})
    payload = await queue.get()
    assert payload["type"] == "patch"
    assert payload["changes"].get("commander.name") == "X"


async def test_enrichment_slot() -> None:
    store = StateStore()
    await store.apply_enrichment("edsm", {"bodies": 5})
    assert store.snapshot["enrichment"]["edsm"] == {"bodies": 5}


def test_diff_dict_nested() -> None:
    old = {"a": {"b": 1, "c": 2}}
    new = {"a": {"b": 1, "c": 3}}
    assert diff_dict(old, new) == {"a.c": 3}
