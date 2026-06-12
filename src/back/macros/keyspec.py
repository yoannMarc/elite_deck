"""Représentation riche d'une touche (``KeySpec``).

Une touche peut être définie de plusieurs façons, par ordre de priorité :
  1. ``vk``   — code virtuel (entier). Permet de cibler une touche absente du
                clavier physique mais détectable par Elite Dangerous (ex. F13).
  2. ``name`` — nom de touche spéciale (``home``, ``f7``, ``numpad_0``…).
  3. ``char`` — caractère imprimable (``g``, ``,``…).

``scan`` (code de scan) est optionnel et réservé à un backend DirectInput pour
une compatibilité jeu maximale (voir engine.py).

Le tout est sérialisable pour transiter par WebSocket et être persisté.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Final

# ── Tables de codes virtuels Windows (VK) utiles ──────────────────────────────
# Surtout les touches « étendues » que ED détecte mais qui manquent souvent
# physiquement : F13-F24. Source : Microsoft Virtual-Key Codes.
NAME_TO_VK: Final[dict[str, int]] = {
    "f13": 0x7C, "f14": 0x7D, "f15": 0x7E, "f16": 0x7F,
    "f17": 0x80, "f18": 0x81, "f19": 0x82, "f20": 0x83,
    "f21": 0x84, "f22": 0x85, "f23": 0x86, "f24": 0x87,
    # Pavé numérique explicite
    "numpad_0": 0x60, "numpad_1": 0x61, "numpad_2": 0x62, "numpad_3": 0x63,
    "numpad_4": 0x64, "numpad_5": 0x65, "numpad_6": 0x66, "numpad_7": 0x67,
    "numpad_8": 0x68, "numpad_9": 0x69,
    "numpad_multiply": 0x6A, "numpad_add": 0x6B, "numpad_subtract": 0x6D,
    "numpad_decimal": 0x6E, "numpad_divide": 0x6F,
}
VK_TO_NAME: Final[dict[int, str]] = {vk: name for name, vk in NAME_TO_VK.items()}

# Modificateurs reconnus
MODIFIERS: Final[frozenset[str]] = frozenset({"ctrl", "shift", "alt", "win", "cmd"})


@dataclass(slots=True)
class KeySpec:
    """Définition complète d'une touche à envoyer."""

    char: str | None = None
    name: str | None = None
    vk: int | None = None
    scan: int | None = None
    modifiers: list[str] = field(default_factory=list)
    label: str = ""  # libellé lisible pour l'UI

    # ── Sérialisation ─────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "char": self.char,
            "name": self.name,
            "vk": self.vk,
            "scan": self.scan,
            "modifiers": list(self.modifiers),
            "label": self.label or self.display(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KeySpec:
        spec = cls(
            char=data.get("char"),
            name=data.get("name"),
            vk=data.get("vk"),
            scan=data.get("scan"),
            modifiers=list(data.get("modifiers", [])),
            label=data.get("label", ""),
        )
        if not spec.label:
            spec.label = spec.display()
        return spec

    # ── Construction depuis une chaîne legacy ─────────────────────────

    @classmethod
    def parse(cls, keybind: str) -> KeySpec:
        """Construit un KeySpec depuis ``"ctrl+shift+g"`` ou ``"f13"``."""
        if not keybind:
            return cls()
        parts = [p.strip() for p in keybind.split("+") if p.strip()]
        modifiers: list[str] = []
        key_part = ""
        for part in parts:
            low = part.lower()
            if low in MODIFIERS:
                modifiers.append(low)
            else:
                key_part = low

        spec = cls(modifiers=modifiers)
        if not key_part:
            pass
        elif key_part in NAME_TO_VK:
            spec.vk = NAME_TO_VK[key_part]
            spec.name = key_part
        elif len(key_part) == 1:
            spec.char = key_part
        else:
            spec.name = key_part  # home, end, f7, enter…
        spec.label = spec.display()
        return spec

    # ── Affichage ─────────────────────────────────────────────────────

    def display(self) -> str:
        """Libellé lisible : ``Ctrl+Shift+G``, ``F13``, ``VK 135``…"""
        if self.name:
            base = self.name.upper().replace("_", " ")
        elif self.char:
            base = self.char.upper()
        elif self.vk is not None:
            base = VK_TO_NAME.get(self.vk, f"VK {self.vk}").upper().replace("_", " ")
        else:
            base = "—"
        if self.modifiers:
            prefix = "+".join(m.capitalize() for m in self.modifiers)
            return f"{prefix}+{base}"
        return base

    def is_empty(self) -> bool:
        return self.char is None and self.name is None and self.vk is None
