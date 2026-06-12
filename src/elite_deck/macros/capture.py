"""Service de capture de touche.

Permet de configurer une macro « par détection » : on écoute le clavier du PC
et on capture la prochaine touche pressée (avec ses modificateurs), puis on la
convertit en ``KeySpec``.

La capture a lieu **sur le PC** (où tourne pynput), pas dans le navigateur de la
tablette : la touche doit être une touche qu'Elite Dangerous peut détecter.

Le backend de capture est abstrait pour rester testable sans clavier réel.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Protocol

from elite_deck.macros.keyspec import VK_TO_NAME, KeySpec

logger = logging.getLogger(__name__)

_MODIFIER_VKS = {
    0xA0: "shift", 0xA1: "shift", 0x10: "shift",
    0xA2: "ctrl", 0xA3: "ctrl", 0x11: "ctrl",
    0xA4: "alt", 0xA5: "alt", 0x12: "alt",
    0x5B: "win", 0x5C: "win",
}


class CaptureBackend(Protocol):
    """Contrat d'un backend de capture de touche."""

    async def capture(self, timeout: float) -> KeySpec | None:
        """Capture la prochaine touche, ou ``None`` si timeout/annulation."""
        ...


class NullCaptureBackend:
    """Backend de capture factice (tests) : renvoie un KeySpec préprogrammé."""

    def __init__(self, preset: KeySpec | None = None) -> None:
        self.preset = preset

    async def capture(self, timeout: float) -> KeySpec | None:
        return self.preset


class PynputCaptureBackend:
    """Capture réelle via un listener pynput one-shot."""

    def __init__(self) -> None:
        # Vérifie la disponibilité au plus tôt
        from pynput import keyboard  # noqa: F401

    async def capture(self, timeout: float) -> KeySpec | None:
        from pynput import keyboard

        loop = asyncio.get_running_loop()
        future: asyncio.Future[KeySpec | None] = loop.create_future()
        held_modifiers: set[str] = set()

        def on_press(key: object) -> bool | None:
            vk = getattr(key, "vk", None)
            # Suivi des modificateurs maintenus
            if vk in _MODIFIER_VKS:
                held_modifiers.add(_MODIFIER_VKS[vk])
                return None  # on attend la touche principale

            spec = _keyspec_from_pynput(key, sorted(held_modifiers))
            if spec is not None and not future.done():
                loop.call_soon_threadsafe(future.set_result, spec)
            return False  # arrête le listener

        def on_release(key: object) -> None:
            vk = getattr(key, "vk", None)
            if vk in _MODIFIER_VKS:
                held_modifiers.discard(_MODIFIER_VKS[vk])

        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.start()
        try:
            return await asyncio.wait_for(future, timeout)
        except TimeoutError:
            return None
        finally:
            listener.stop()


def _keyspec_from_pynput(key: object, modifiers: list[str]) -> KeySpec | None:
    """Convertit une touche pynput (Key ou KeyCode) en KeySpec."""
    char = getattr(key, "char", None)
    vk = getattr(key, "vk", None)
    name = getattr(key, "name", None)  # présent sur les Key spéciales

    spec: KeySpec
    if name:  # touche spéciale (home, f7, enter…)
        spec = KeySpec(name=name, vk=vk, modifiers=modifiers)
    elif char:  # caractère imprimable
        spec = KeySpec(char=char, vk=vk, modifiers=modifiers)
    elif vk is not None:  # touche sans caractère (F13, media…)
        spec = KeySpec(vk=vk, name=VK_TO_NAME.get(vk), modifiers=modifiers)
    else:
        return None
    spec.label = spec.display()
    return spec


class KeyCaptureService:
    """Façade de capture, avec verrou pour une seule capture à la fois."""

    def __init__(self, backend: CaptureBackend | None = None) -> None:
        self.backend = backend or _auto_capture_backend()
        self._lock = asyncio.Lock()

    async def capture(self, timeout: float = 10.0) -> KeySpec | None:
        if self._lock.locked():
            logger.warning("Capture déjà en cours")
            return None
        async with self._lock:
            return await self.backend.capture(timeout)


def _auto_capture_backend() -> CaptureBackend:
    try:
        return PynputCaptureBackend()
    except Exception as exc:  # pynput absent / headless
        logger.warning("Capture indisponible (%s) — NullCaptureBackend", exc)
        return NullCaptureBackend()
