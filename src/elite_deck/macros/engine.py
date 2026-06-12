"""Moteur de macros — envoi de touches au jeu.

Le backend d'envoi est abstrait derrière un ``Protocol`` pour rester testable
et permettre de changer de bibliothèque (pynput, pyautogui…) sans toucher au
reste du code. Le backend réel n'est chargé que sur le PC qui fait tourner le
jeu ; en environnement de test/headless, on injecte un backend factice.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Protocol

logger = logging.getLogger(__name__)


# ── Backend abstrait ──────────────────────────────────────────────────────────


class KeyBackend(Protocol):
    """Contrat d'un backend capable d'envoyer des frappes clavier."""

    def tap(self, key: str, modifiers: list[str]) -> None:
        """Appuie puis relâche ``key`` avec d'éventuels modificateurs."""
        ...


class NullBackend:
    """Backend factice : journalise sans rien envoyer (tests, CI, headless)."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, list[str]]] = []

    def tap(self, key: str, modifiers: list[str]) -> None:
        self.sent.append((key, modifiers))
        logger.info("[NullBackend] tap %s + %s", modifiers, key)


class PynputBackend:
    """Backend réel basé sur pynput (chargé uniquement si disponible)."""

    def __init__(self) -> None:
        from pynput.keyboard import Controller  # import paresseux

        self._controller = Controller()

    def tap(self, key: str, modifiers: list[str]) -> None:
        from pynput.keyboard import Key

        def resolve(name: str) -> object:
            special = getattr(Key, name.lower(), None)
            return special if special is not None else name

        mods = [resolve(m) for m in modifiers]
        target = resolve(key)
        for mod in mods:
            self._controller.press(mod)
        self._controller.press(target)
        self._controller.release(target)
        for mod in reversed(mods):
            self._controller.release(mod)


def auto_backend() -> KeyBackend:
    """Retourne le meilleur backend disponible, sinon ``NullBackend``."""
    try:
        return PynputBackend()
    except Exception as exc:  # pynput absent ou pas d'affichage
        logger.warning("Backend clavier indisponible (%s) — NullBackend utilisé", exc)
        return NullBackend()


# ── Parsing des raccourcis ────────────────────────────────────────────────────

_MODIFIERS = {"CTRL", "SHIFT", "ALT", "WIN", "CMD"}


def parse_keybind(keybind: str) -> tuple[list[str], str]:
    """``"CTRL+SHIFT+G"`` → ``(["ctrl", "shift"], "g")``."""
    if not keybind:
        return [], ""
    parts = [p.strip() for p in keybind.split("+") if p.strip()]
    modifiers: list[str] = []
    key = ""
    for part in parts:
        upper = part.upper()
        if upper in _MODIFIERS:
            modifiers.append(upper.lower())
        else:
            key = part.lower()
    return modifiers, key


# ── Moteur ────────────────────────────────────────────────────────────────────


class MacroEngine:
    """Exécute des macros (frappe simple ou séquence) via le backend."""

    def __init__(self, backend: KeyBackend | None = None) -> None:
        self.backend = backend or auto_backend()

    def send(self, keybind: str, *, delay: float = 0.0) -> None:
        """Envoie une frappe unique (dans un thread pour ne pas bloquer)."""
        modifiers, key = parse_keybind(keybind)
        if not key:
            return

        def _run() -> None:
            if delay:
                time.sleep(delay)
            self.backend.tap(key, modifiers)

        threading.Thread(target=_run, daemon=True).start()

    def send_sequence(self, keybinds: list[str], *, gap: float = 0.2) -> None:
        """Envoie une séquence de frappes espacées de ``gap`` secondes."""

        def _run() -> None:
            for kb in keybinds:
                modifiers, key = parse_keybind(kb)
                if key:
                    self.backend.tap(key, modifiers)
                time.sleep(gap)

        threading.Thread(target=_run, daemon=True).start()
