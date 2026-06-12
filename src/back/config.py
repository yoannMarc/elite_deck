"""Configuration typée de l'application.

Chargée depuis un fichier TOML optionnel (``tomllib`` stdlib, Python ≥ 3.11),
avec valeurs par défaut. Conçue pour être facilement remplaçable par
``pydantic-settings`` si le projet grossit, sans changer les appelants.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 3300


@dataclass(slots=True)
class IngestConfig:
    journal_dir: str = ""        # vide = auto-détection
    replay_history: bool = True
    poll_interval: float = 0.4


@dataclass(slots=True)
class IntegrationsConfig:
    edsm_enabled: bool = False
    fdevids_enabled: bool = False


@dataclass(slots=True)
class AppConfig:
    server: ServerConfig = field(default_factory=ServerConfig)
    ingest: IngestConfig = field(default_factory=IngestConfig)
    integrations: IntegrationsConfig = field(default_factory=IntegrationsConfig)
    # Surcharges de keybinds : {macro_id: "ctrl+g"}
    keybinds: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path | None = None) -> AppConfig:
        """Charge la config depuis un TOML, ou retourne les défauts."""
        cfg = cls()
        if path is None or not path.exists():
            return cfg
        with open(path, "rb") as fh:
            data: dict[str, Any] = tomllib.load(fh)

        if "server" in data:
            cfg.server = ServerConfig(**data["server"])
        if "ingest" in data:
            cfg.ingest = IngestConfig(**data["ingest"])
        if "integrations" in data:
            cfg.integrations = IntegrationsConfig(**data["integrations"])
        if "keybinds" in data:
            cfg.keybinds = dict(data["keybinds"])
        return cfg
