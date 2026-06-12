"""Watcher asynchrone des fichiers du jeu Elite Dangerous.

- ``Journal.*.log`` : append-only avec rotation, suivi ligne par ligne.
- Fichiers d'état (``Status.json``, ``Cargo.json``, ``NavRoute.json``…) :
  réécrits entièrement, surveillés au mtime.
"""

from __future__ import annotations

import asyncio
import glob
import json
import logging
import os
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

EventCallback = Callable[[dict[str, Any]], Awaitable[None]]
FileCallback = Callable[[str, dict[str, Any]], Awaitable[None]]

STATUS_FILES: tuple[str, ...] = (
    "Status.json",
    "Cargo.json",
    "NavRoute.json",
    "Market.json",
    "Outfitting.json",
    "Shipyard.json",
    "ModulesInfo.json",
    "Backpack.json",
    "ShipLocker.json",
)


def default_journal_dir() -> Path:
    """Dossier par défaut des logs ED (Windows + fallback Wine/Proton)."""
    win = Path.home() / "Saved Games" / "Frontier Developments" / "Elite Dangerous"
    if win.exists():
        return win
    try:
        user = os.getlogin()
    except OSError:
        user = os.environ.get("USER", os.environ.get("USERNAME", "user"))
    wine = (
        Path.home() / ".wine" / "drive_c" / "users" / user
        / "Saved Games" / "Frontier Developments" / "Elite Dangerous"
    )
    return wine if wine.exists() else win


def _latest_journal(journal_dir: Path) -> Path | None:
    files = glob.glob(str(journal_dir / "Journal.*.log"))
    return Path(max(files, key=os.path.getmtime)) if files else None


class JournalWatcher:
    """Suit les fichiers du jeu et déclenche des callbacks asynchrones."""

    def __init__(
        self,
        journal_dir: Path | None = None,
        on_event: EventCallback | None = None,
        on_file: FileCallback | None = None,
        *,
        replay_history: bool = True,
        poll_interval: float = 0.4,
    ) -> None:
        self.dir = Path(journal_dir) if journal_dir else default_journal_dir()
        self.on_event = on_event
        self.on_file = on_file
        self.replay_history = replay_history
        self.poll_interval = poll_interval

        self._running = False
        self._current_journal: Path | None = None
        self._journal_pos = 0
        self._mtimes: dict[str, float] = {}

    async def start(self) -> None:
        self._running = True
        await self._init_journal()
        await asyncio.gather(self._watch_journal(), self._watch_status_files())

    def stop(self) -> None:
        self._running = False

    # ── Journal ───────────────────────────────────────────────────────

    async def _init_journal(self) -> None:
        latest = _latest_journal(self.dir)
        if latest is None:
            return
        self._current_journal = latest
        if self.replay_history:
            self._journal_pos = await self._read_journal_from(0)
        else:
            self._journal_pos = latest.stat().st_size

    async def _read_journal_from(self, start_pos: int) -> int:
        if self._current_journal is None or not self._current_journal.exists():
            return start_pos
        try:
            with open(self._current_journal, encoding="utf-8") as fh:
                fh.seek(start_pos)
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if self.on_event:
                        await self.on_event(event)
                return fh.tell()
        except OSError:
            return start_pos

    async def _watch_journal(self) -> None:
        while self._running:
            await asyncio.sleep(self.poll_interval)
            latest = _latest_journal(self.dir)
            if latest and latest != self._current_journal:
                self._current_journal = latest
                self._journal_pos = 0
            self._journal_pos = await self._read_journal_from(self._journal_pos)

    # ── Fichiers d'état ───────────────────────────────────────────────

    async def _watch_status_files(self) -> None:
        while self._running:
            await asyncio.sleep(self.poll_interval)
            for fname in STATUS_FILES:
                await self._check_file(fname)

    async def _check_file(self, fname: str) -> None:
        path = self.dir / fname
        if not path.exists():
            return
        try:
            mtime = path.stat().st_mtime
        except OSError:
            return
        if self._mtimes.get(fname) == mtime:
            return
        self._mtimes[fname] = mtime
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, OSError):
            return
        if self.on_file:
            await self.on_file(fname, data)
