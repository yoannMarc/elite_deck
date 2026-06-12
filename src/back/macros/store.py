"""Persistance des raccourcis configurés par l'utilisateur.

Stocke un mapping ``{macro_id: KeySpec}`` dans un fichier JSON, séparé de la
config TOML (qui ne fournit que les valeurs initiales). Ce fichier est réécrit à
chaque modification faite depuis l'interface.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from back.macros.keyspec import KeySpec

logger = logging.getLogger(__name__)


def default_keybinds_path() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home() / ".config"
    return base / "back" / "keybinds.json"


class KeybindStore:
    """Charge / sauvegarde les KeySpec par identifiant de macro."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_keybinds_path()
        self._data: dict[str, KeySpec] = {}
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Lecture keybinds impossible : %s", exc)
            return
        self._data = {
            macro_id: KeySpec.from_dict(spec) for macro_id, spec in raw.items()
        }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {macro_id: spec.to_dict() for macro_id, spec in self._data.items()}
        try:
            self.path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except OSError as exc:
            logger.warning("Écriture keybinds impossible : %s", exc)

    def get(self, macro_id: str) -> KeySpec | None:
        return self._data.get(macro_id)

    def set(self, macro_id: str, spec: KeySpec) -> None:
        self._data[macro_id] = spec
        self.save()

    def all(self) -> dict[str, KeySpec]:
        return dict(self._data)
