"""Modèles d'état typés du jeu.

Le ``GameState`` est l'unique source de vérité, reconstruit depuis les fichiers
du jeu. Le champ ``enrichment`` est réservé aux données ajoutées par les
intégrations externes (EDSM, FDevIDs…) sans toucher au noyau.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Commander:
    name: str = ""
    credits: int = 0
    game_mode: str = ""


@dataclass(slots=True)
class Ship:
    type: str = ""
    type_label: str = ""  # nom lisible, rempli par l'intégration FDevIDs (futur)
    name: str = ""
    ident: str = ""
    hull_health: float = 100.0
    fuel_main: float = 0.0
    fuel_cap: float = 0.0
    cargo: int = 0
    cargo_cap: int = 0
    rebuy: int = 0


@dataclass(slots=True)
class Status:
    docked: bool = False
    landed: bool = False
    landing_gear: bool = False
    shields: bool = True
    supercruise: bool = False
    flight_assist_off: bool = False
    hardpoints: bool = False
    cargo_scoop: bool = False
    lights: bool = False
    silent_running: bool = False
    fsd_charging: bool = False
    fsd_cooldown: bool = False
    fsd_masslock: bool = False
    low_fuel: bool = False
    overheating: bool = False
    in_danger: bool = False
    being_interdicted: bool = False
    analysis_mode: bool = False
    night_vision: bool = False
    sco_active: bool = False
    on_foot: bool = False
    pips: list[int] = field(default_factory=lambda: [2, 2, 2])
    fire_group: int = 0
    gui_focus: int = 0
    legal_state: str = "Clean"


@dataclass(slots=True)
class Navigation:
    system: str = ""
    body: str = ""
    station: str = ""
    station_type: str = ""
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None
    heading: int | None = None
    route: list[str] = field(default_factory=list)
    jumps_remaining: int = 0


@dataclass(slots=True)
class CargoItem:
    name: str
    count: int


@dataclass(slots=True)
class GameState:
    connected: bool = False
    commander: Commander = field(default_factory=Commander)
    ship: Ship = field(default_factory=Ship)
    status: Status = field(default_factory=Status)
    navigation: Navigation = field(default_factory=Navigation)
    cargo: list[CargoItem] = field(default_factory=list)
    # Données ajoutées par les intégrations externes (futur). Clé = nom du
    # provider (ex. "edsm"), valeur = payload libre.
    enrichment: dict[str, Any] = field(default_factory=dict)
    last_event: str = ""
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
