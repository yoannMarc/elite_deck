"""Tests du moteur et du registre de macros."""

from __future__ import annotations

import time

from elite_deck.macros.engine import MacroEngine, NullBackend, parse_keybind
from elite_deck.macros.registry import MacroRegistry


def test_parse_keybind_simple() -> None:
    assert parse_keybind("g") == ([], "g")
    assert parse_keybind("f7") == ([], "f7")


def test_parse_keybind_modifiers() -> None:
    mods, key = parse_keybind("CTRL+SHIFT+G")
    assert mods == ["ctrl", "shift"]
    assert key == "g"


def test_engine_sends_via_backend() -> None:
    backend = NullBackend()
    engine = MacroEngine(backend=backend)
    engine.send("ctrl+g")
    time.sleep(0.1)  # le send est threadé
    assert backend.sent == [("g", ["ctrl"])]


def test_engine_sequence() -> None:
    backend = NullBackend()
    engine = MacroEngine(backend=backend)
    engine.send_sequence(["g", "home"], gap=0.01)
    time.sleep(0.1)
    assert backend.sent == [("g", []), ("home", [])]


def test_registry_keybind_override() -> None:
    reg = MacroRegistry()
    reg.apply_keybinds({"landing_gear": "ctrl+g"})
    macro = reg.get("landing_gear")
    assert macro is not None
    assert macro.keybind == "ctrl+g"


def test_registry_client_list_hides_keybinds() -> None:
    reg = MacroRegistry()
    client = reg.to_client_list()
    assert all("keybind" not in m for m in client)
    assert any(m["id"] == "landing_gear" for m in client)
