"""Décodage des drapeaux ``Status.json`` (Flags / Flags2).

Référence : https://elite-journal.readthedocs.io/en/latest/Status%20File.html
"""

from __future__ import annotations

from typing import Final

FLAGS: Final[dict[str, int]] = {
    "docked": 1 << 0,
    "landed": 1 << 1,
    "landing_gear": 1 << 2,
    "shields": 1 << 3,
    "supercruise": 1 << 4,
    "flight_assist_off": 1 << 5,
    "hardpoints": 1 << 6,
    "in_wing": 1 << 7,
    "lights": 1 << 8,
    "cargo_scoop": 1 << 9,
    "silent_running": 1 << 10,
    "scooping_fuel": 1 << 11,
    "fsd_masslock": 1 << 16,
    "fsd_charging": 1 << 17,
    "fsd_cooldown": 1 << 18,
    "low_fuel": 1 << 19,
    "overheating": 1 << 20,
    "has_lat_long": 1 << 21,
    "in_danger": 1 << 22,
    "being_interdicted": 1 << 23,
    "in_main_ship": 1 << 24,
    "in_fighter": 1 << 25,
    "in_srv": 1 << 26,
    "analysis_mode": 1 << 27,
    "night_vision": 1 << 28,
    "fsd_jump": 1 << 30,
}

FLAGS2: Final[dict[str, int]] = {
    "on_foot": 1 << 0,
    "in_taxi": 1 << 1,
    "in_multicrew": 1 << 2,
    "on_foot_in_station": 1 << 3,
    "on_foot_on_planet": 1 << 4,
    "low_oxygen": 1 << 6,
    "low_health": 1 << 7,
    "glide_mode": 1 << 12,
    "breathable_atmos": 1 << 16,
    "sco_active": 1 << 20,
    "sca_active": 1 << 21,
}


def decode_flags(value: int, table: dict[str, int]) -> dict[str, bool]:
    """Décode un entier bitmask en ``{nom: bool}``."""
    return {name: bool(value & mask) for name, mask in table.items()}
