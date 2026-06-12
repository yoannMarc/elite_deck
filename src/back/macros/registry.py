"""Registre des macros.

Une macro lie un identifiant stable (utilisé par le client) à une touche
(``KeySpec``, configurable) et à des métadonnées d'affichage. Le registre est
sérialisable pour être envoyé au client (qui dessine les boutons et l'interface
de configuration) et exécuté par le serveur.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from back.macros.keyspec import KeySpec


@dataclass(slots=True)
class Macro:
    id: str
    label: str
    key: KeySpec = field(default_factory=KeySpec)
    # "tap" (frappe simple) ou "sequence" (plusieurs frappes)
    kind: str = "tap"
    sequence: list[KeySpec] = field(default_factory=list)
    # Drapeau d'état (Status) reflété par le bouton, si applicable.
    status_flag: str = ""
    category: str = "ship"
    accent: str = "orange"

    def to_dict(self) -> dict[str, Any]:
        """Sérialisation envoyée au client (avec la touche, pour configuration)."""
        return {
            "id": self.id,
            "label": self.label,
            "kind": self.kind,
            "status_flag": self.status_flag,
            "category": self.category,
            "accent": self.accent,
            "key": self.key.to_dict(),
            "sequence": [s.to_dict() for s in self.sequence],
        }


def _k(keybind: str) -> KeySpec:
    return KeySpec.parse(keybind)


# Macros par défaut. Les raccourcis doivent correspondre à ceux configurés
# dans Elite Dangerous (Options → Commandes).
DEFAULT_MACROS: list[Macro] = [
    Macro("landing_gear", "Train", _k("g"), status_flag="landing_gear",
          category="flight", accent="amber"),
    Macro("hardpoints", "Armes", _k("u"), status_flag="hardpoints",
          category="combat", accent="red"),
    Macro("cargo_scoop", "Cargo scoop", _k("home"), status_flag="cargo_scoop",
          category="flight", accent="green"),
    Macro("lights", "Lumières", _k("insert"), status_flag="lights",
          category="flight", accent="amber"),
    Macro("night_vision", "Vision nuit", _k("f12"), status_flag="night_vision",
          category="flight", accent="blue"),
    Macro("analysis_mode", "Mode analyse", _k("f7"), status_flag="analysis_mode",
          category="combat", accent="blue"),
    Macro("silent_running", "Silent running", _k("delete"),
          status_flag="silent_running", category="combat", accent="red"),
    Macro("sys_power", "▲ SYS", _k("f1"), category="power", accent="blue"),
    Macro("eng_power", "▲ ENG", _k("f2"), category="power", accent="green"),
    Macro("wep_power", "▲ WEP", _k("f3"), category="power", accent="red"),
    Macro("landing_combo", "Approche", KeySpec(), kind="sequence",
          sequence=[_k("g"), _k("home")], category="combo", accent="amber"),
    Macro("combat_ready", "Combat", KeySpec(), kind="sequence",
          sequence=[_k("u"), _k("f3")], category="combo", accent="red"),
]


class MacroRegistry:
    """Conteneur indexé des macros, avec surcharge des touches par config."""

    def __init__(self, macros: list[Macro] | None = None) -> None:
        import copy

        self._macros: dict[str, Macro] = {}
        for macro in macros or copy.deepcopy(DEFAULT_MACROS):
            self._macros[macro.id] = macro

    def get(self, macro_id: str) -> Macro | None:
        return self._macros.get(macro_id)

    def all(self) -> list[Macro]:
        return list(self._macros.values())

    def to_client_list(self) -> list[dict[str, Any]]:
        return [m.to_dict() for m in self._macros.values()]

    def apply_keyspecs(self, overrides: dict[str, KeySpec]) -> None:
        """Surcharge les touches depuis le store de persistance."""
        for macro_id, spec in overrides.items():
            macro = self._macros.get(macro_id)
            if macro is not None:
                macro.key = spec

    def apply_keybind_strings(self, overrides: dict[str, str]) -> None:
        """Surcharge depuis des chaînes (config TOML legacy)."""
        for macro_id, keybind in overrides.items():
            macro = self._macros.get(macro_id)
            if macro is not None:
                macro.key = KeySpec.parse(keybind)

    def set_key(self, macro_id: str, spec: KeySpec) -> bool:
        macro = self._macros.get(macro_id)
        if macro is None:
            return False
        macro.key = spec
        return True
