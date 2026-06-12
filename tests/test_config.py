"""Tests de la capture de touche et de la persistance des raccourcis."""

from __future__ import annotations

from pathlib import Path

from back.macros.capture import KeyCaptureService, NullCaptureBackend
from back.macros.keyspec import KeySpec
from back.macros.store import KeybindStore


async def test_capture_returns_preset() -> None:
    preset = KeySpec.parse("f13")
    service = KeyCaptureService(backend=NullCaptureBackend(preset))
    spec = await service.capture(timeout=1.0)
    assert spec is not None
    assert spec.vk == preset.vk


async def test_capture_none_when_no_preset() -> None:
    service = KeyCaptureService(backend=NullCaptureBackend(None))
    spec = await service.capture(timeout=1.0)
    assert spec is None


def test_keybind_store_persists(tmp_path: Path) -> None:
    path = tmp_path / "keybinds.json"
    store = KeybindStore(path=path)
    store.set("landing_gear", KeySpec.parse("ctrl+f13"))

    # Recharge depuis le disque
    reloaded = KeybindStore(path=path)
    spec = reloaded.get("landing_gear")
    assert spec is not None
    assert spec.modifiers == ["ctrl"]
    assert spec.display() == "Ctrl+F13"


def test_keybind_store_empty_when_absent(tmp_path: Path) -> None:
    store = KeybindStore(path=tmp_path / "nope.json")
    assert store.all() == {}
