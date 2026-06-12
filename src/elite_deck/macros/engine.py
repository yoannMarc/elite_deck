"""Moteur de macros — envoi de touches au jeu.

Le backend d'envoi est abstrait derrière un ``Protocol`` pour rester testable
et permettre de changer d'implémentation sans toucher au reste du code :
  - ``NullBackend``     : factice (tests, headless) — enregistre les envois.
  - ``PynputBackend``   : envoi via pynput (VK codes), bon défaut multiplateforme.
  - ``ScanCodeBackend`` : envoi par code de scan via SendInput (Windows).
                          Plus fiable pour les jeux DirectInput comme ED, qui
                          lisent souvent les scan codes plutôt que les VK.

Tous les backends reçoivent un ``KeySpec`` (pas une chaîne) : on supporte ainsi
les caractères, les touches nommées et les **codes virtuels** (ex. F13).
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Protocol

from elite_deck.macros.keyspec import NAME_TO_VK, KeySpec

logger = logging.getLogger(__name__)


# ── Backend abstrait ──────────────────────────────────────────────────────────


class KeyBackend(Protocol):
    """Contrat d'un backend capable d'envoyer une frappe."""

    def tap(self, spec: KeySpec) -> None:
        """Appuie puis relâche la touche décrite par ``spec``."""
        ...


class NullBackend:
    """Backend factice : journalise sans rien envoyer (tests, CI, headless)."""

    def __init__(self) -> None:
        self.sent: list[KeySpec] = []

    def tap(self, spec: KeySpec) -> None:
        self.sent.append(spec)
        logger.info("[NullBackend] tap %s", spec.display())


class PynputBackend:
    """Backend réel basé sur pynput (envoi par VK / caractère)."""

    def __init__(self) -> None:
        from pynput.keyboard import Controller  # import paresseux

        self._controller = Controller()

    def _resolve(self, spec_or_modifier: KeySpec | str) -> object:
        from pynput.keyboard import Key, KeyCode

        if isinstance(spec_or_modifier, str):
            return getattr(Key, spec_or_modifier.lower(), spec_or_modifier)

        spec = spec_or_modifier
        if spec.vk is not None:
            return KeyCode.from_vk(spec.vk)
        if spec.name:
            special = getattr(Key, spec.name.lower(), None)
            if special is not None:
                return special
            vk = NAME_TO_VK.get(spec.name.lower())
            if vk is not None:
                return KeyCode.from_vk(vk)
            return KeyCode.from_char(spec.name)
        if spec.char:
            return KeyCode.from_char(spec.char)
        raise ValueError("KeySpec vide")

    def tap(self, spec: KeySpec) -> None:
        target = self._resolve(spec)
        mods = [self._resolve(m) for m in spec.modifiers]
        for mod in mods:
            self._controller.press(mod)
        self._controller.press(target)
        self._controller.release(target)
        for mod in reversed(mods):
            self._controller.release(mod)


class ScanCodeBackend:
    """Backend Windows par code de scan (SendInput, KEYEVENTF_SCANCODE).

    Recommandé pour Elite Dangerous : de nombreux jeux DirectInput lisent les
    codes de scan matériels et ignorent les VK injectés via le message système.
    Nécessite un ``KeySpec.scan`` renseigné (à défaut, lève ``ValueError``).

    NB : implémentation Windows uniquement, non testée en environnement headless.
    """

    def __init__(self) -> None:
        import ctypes

        if not hasattr(ctypes, "windll"):
            raise RuntimeError("ScanCodeBackend disponible uniquement sur Windows")

    def tap(self, spec: KeySpec) -> None:
        if spec.scan is None:
            raise ValueError("ScanCodeBackend requiert un scan code")
        import ctypes

        keyeventf_scancode = 0x0008
        keyeventf_keyup = 0x0002
        user32 = ctypes.windll.user32  # type: ignore[attr-defined]
        user32.keybd_event(0, spec.scan, keyeventf_scancode, 0)
        user32.keybd_event(0, spec.scan, keyeventf_scancode | keyeventf_keyup, 0)


def auto_backend() -> KeyBackend:
    """Retourne le meilleur backend disponible, sinon ``NullBackend``."""
    try:
        return PynputBackend()
    except Exception as exc:  # pynput absent ou pas d'affichage
        logger.warning("Backend clavier indisponible (%s) — NullBackend utilisé", exc)
        return NullBackend()


# ── Moteur ────────────────────────────────────────────────────────────────────


class MacroEngine:
    """Exécute des macros (frappe simple ou séquence) via le backend."""

    def __init__(self, backend: KeyBackend | None = None) -> None:
        self.backend = backend or auto_backend()

    def tap(self, spec: KeySpec, *, delay: float = 0.0) -> None:
        """Envoie une frappe unique (dans un thread pour ne pas bloquer)."""
        if spec.is_empty():
            return

        def _run() -> None:
            if delay:
                time.sleep(delay)
            self.backend.tap(spec)

        threading.Thread(target=_run, daemon=True).start()

    def tap_sequence(self, specs: list[KeySpec], *, gap: float = 0.2) -> None:
        """Envoie une séquence de frappes espacées de ``gap`` secondes."""

        def _run() -> None:
            for spec in specs:
                if not spec.is_empty():
                    self.backend.tap(spec)
                time.sleep(gap)

        threading.Thread(target=_run, daemon=True).start()
