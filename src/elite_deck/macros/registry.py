"""Registre des macros.

Une macro lie un identifiant stable (utilisé par le client web) à un raccourci
clavier configurable et à des métadonnées d'affichage. Le registre est
sérialisable pour être envoyé au client (qui dessine les boutons) et exécuté
par le serveur.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Macro:
    id: str
    label: str
    keybind: str
    # Type de macro : "tap" (frappe simple) ou "sequence" (plusieurs frappes)
    kind: str = "tap"
    sequence: list[str] = field(default_factory=list)
    # Drapeau d'état (Status) reflété par le bouton, si applicable.
    # Permet au client d'allumer le bouton quand l'action est active.
    status_flag: str = ""
    # Catégorie d'affichage (regroupement dans l'UI)
    category: str = "ship"
    # Couleur d'accent suggérée (le client peut l'ignorer)
    accent: str = "orange"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "kind": self.kind,
            "status_flag": self.status_flag,
            "category": self.category,
            "accent": self.accent,
            # le keybind n'est pas exposé au client : il reste côté serveur
        }


# Macros par défaut. Les keybinds doivent correspondre à ceux configurés
# dans Elite Dangerous (Options → Commandes).
DEFAULT_MACROS: list[Macro] = [
    Macro("landing_gear", "Train", "g", status_flag="landing_gear",
          category="flight", accent="amber"),
    Macro("hardpoints", "Armes", "u", status_flag="hardpoints",
          category="combat", accent="red"),
    Macro("cargo_scoop", "Cargo scoop", "home", status_flag="cargo_scoop",
          category="flight", accent="green"),
    Macro("lights", "Lumières", "insert", status_flag="lights",
          category="flight", accent="amber"),
    Macro("night_vision", "Vision nuit", "f12", status_flag="night_vision",
          category="flight", accent="blue"),
    Macro("analysis_mode", "Mode analyse", "f7", status_flag="analysis_mode",
          category="combat", accent="blue"),
    Macro("silent_running", "Silent running", "delete", status_flag="silent_running",
          category="combat", accent="red"),
    Macro("sys_power", "▲ SYS", "f1", category="power", accent="blue"),
    Macro("eng_power", "▲ ENG", "f2", category="power", accent="green"),
    Macro("wep_power", "▲ WEP", "f3", category="power", accent="red"),
    Macro("landing_combo", "Approche", "", kind="sequence",
          sequence=["g", "home"], category="combo", accent="amber"),
    Macro("combat_ready", "Combat", "", kind="sequence",
          sequence=["u", "f3"], category="combo", accent="red"),
]


class MacroRegistry:
    """Conteneur indexé des macros, avec surcharge de keybinds par config."""

    def __init__(self, macros: list[Macro] | None = None) -> None:
        self._macros: dict[str, Macro] = {}
        for macro in macros or DEFAULT_MACROS:
            self._macros[macro.id] = macro

    def get(self, macro_id: str) -> Macro | None:
        return self._macros.get(macro_id)

    def all(self) -> list[Macro]:
        return list(self._macros.values())

    def to_client_list(self) -> list[dict[str, Any]]:
        """Liste sérialisable envoyée au client (sans les keybinds)."""
        return [m.to_dict() for m in self._macros.values()]

    def apply_keybinds(self, overrides: dict[str, str]) -> None:
        """Surcharge les keybinds depuis la config utilisateur."""
        for macro_id, keybind in overrides.items():
            if macro_id in self._macros:
                self._macros[macro_id].keybind = keybind
