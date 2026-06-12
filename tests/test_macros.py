"""Tests du moteur, du registre et des KeySpec."""

from __future__ import annotations

import time

from back.macros.engine import MacroEngine, NullBackend
from back.macros.keyspec import NAME_TO_VK, KeySpec
from back.macros.registry import MacroRegistry

# ── KeySpec ───────────────────────────────────────────────────────────────────


def test_keyspec_parse_simple() -> None:
    spec = KeySpec.parse("g")
    assert spec.char == "g"
    assert spec.modifiers == []
    assert spec.display() == "G"


def test_keyspec_parse_modifiers() -> None:
    spec = KeySpec.parse("CTRL+SHIFT+G")
    assert spec.char == "g"
    assert spec.modifiers == ["ctrl", "shift"]
    assert spec.display() == "Ctrl+Shift+G"


def test_keyspec_parse_f13_resolves_to_vk() -> None:
    spec = KeySpec.parse("f13")
    assert spec.vk == NAME_TO_VK["f13"]
    assert spec.name == "f13"
    assert spec.display() == "F13"


def test_keyspec_named_key() -> None:
    spec = KeySpec.parse("home")
    assert spec.name == "home"
    assert spec.char is None


def test_keyspec_roundtrip_dict() -> None:
    spec = KeySpec(vk=135, name="f24", modifiers=["ctrl"])
    restored = KeySpec.from_dict(spec.to_dict())
    assert restored.vk == 135
    assert restored.name == "f24"
    assert restored.modifiers == ["ctrl"]
    assert restored.display() == "Ctrl+F24"


def test_keyspec_empty() -> None:
    assert KeySpec().is_empty()
    assert not KeySpec(char="g").is_empty()


# ── Engine ────────────────────────────────────────────────────────────────────


def test_engine_taps_via_backend() -> None:
    backend = NullBackend()
    engine = MacroEngine(backend=backend)
    engine.tap(KeySpec.parse("ctrl+g"))
    time.sleep(0.1)
    assert len(backend.sent) == 1
    assert backend.sent[0].char == "g"
    assert backend.sent[0].modifiers == ["ctrl"]


def test_engine_taps_vk_key() -> None:
    backend = NullBackend()
    engine = MacroEngine(backend=backend)
    engine.tap(KeySpec.parse("f13"))
    time.sleep(0.1)
    assert backend.sent[0].vk == NAME_TO_VK["f13"]


def test_engine_sequence() -> None:
    backend = NullBackend()
    engine = MacroEngine(backend=backend)
    engine.tap_sequence([KeySpec.parse("g"), KeySpec.parse("home")], gap=0.01)
    time.sleep(0.1)
    assert [s.char or s.name for s in backend.sent] == ["g", "home"]


# ── Registry ──────────────────────────────────────────────────────────────────


def test_registry_set_key() -> None:
    reg = MacroRegistry()
    assert reg.set_key("landing_gear", KeySpec.parse("f13"))
    macro = reg.get("landing_gear")
    assert macro is not None
    assert macro.key.vk == NAME_TO_VK["f13"]


def test_registry_client_list_includes_key() -> None:
    reg = MacroRegistry()
    client = reg.to_client_list()
    landing = next(m for m in client if m["id"] == "landing_gear")
    assert "key" in landing
    assert landing["key"]["label"] == "G"
