"""Racine de composition — assemble tous les composants.

C'est le seul endroit qui connaît toutes les pièces : config, store, watcher,
macros, serveur, intégrations. Le reste du code dépend d'abstractions, pas de
cette fonction de câblage (principe d'inversion de dépendances).
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from back.config import AppConfig
from back.core.store import StateStore
from back.ingest.watcher import JournalWatcher, default_journal_dir
from back.integrations.base import IntegrationManager
from back.integrations.edsm import EDSMProvider
from back.integrations.fdevids import FDevIDsProvider
from back.macros.capture import KeyCaptureService
from back.macros.engine import MacroEngine
from back.macros.registry import MacroRegistry
from back.macros.store import KeybindStore
from back.server.app import TerminalServer

logger = logging.getLogger(__name__)


class Application:
    """Conteneur applicatif : construit et fait tourner tout le système."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config

        # Cœur
        self.store = StateStore()

        # Macros
        self.macros = MacroRegistry()
        # Ordre d'application : défauts → keybinds TOML (legacy) → store JSON
        self.macros.apply_keybind_strings(config.keybinds)
        self.keybinds = KeybindStore()
        self.macros.apply_keyspecs(self.keybinds.all())
        self.engine = MacroEngine()  # backend auto-détecté (Null si headless)
        self.capture = KeyCaptureService()  # backend auto-détecté

        # Intégrations (anticipées, désactivées par défaut)
        self.integrations = IntegrationManager([
            EDSMProvider(enabled=config.integrations.edsm_enabled),
            FDevIDsProvider(enabled=config.integrations.fdevids_enabled),
        ])

        # Ingestion
        journal_dir = (
            Path(config.ingest.journal_dir)
            if config.ingest.journal_dir
            else default_journal_dir()
        )
        self.journal_dir = journal_dir
        self.watcher = JournalWatcher(
            journal_dir=journal_dir,
            on_event=self._on_event,
            on_file=self._on_file,
            replay_history=config.ingest.replay_history,
            poll_interval=config.ingest.poll_interval,
        )

        # Serveur
        self.server = TerminalServer(
            self.store, self.macros, self.engine,
            capture=self.capture, keybinds=self.keybinds,
            host=config.server.host, port=config.server.port,
        )

    # ── Routage ingestion → store ─────────────────────────────────────

    async def _on_event(self, event: dict[str, Any]) -> None:
        await self.store.apply_event(event)
        # Déclencheur d'enrichissement : changement de système
        if event.get("event") in ("FSDJump", "CarrierJump", "Location"):
            await self._run_enrichment()

    async def _on_file(self, fname: str, data: dict[str, Any]) -> None:
        if fname == "Status.json":
            await self.store.apply_status(data)
        elif fname == "Cargo.json":
            await self.store.apply_cargo(data)
        elif fname == "NavRoute.json":
            await self.store.apply_navroute(data)
        # Market/Outfitting/Shipyard… : disponibles ici pour traitement futur

    async def _run_enrichment(self) -> None:
        """Interroge les intégrations actives (no-op si aucune)."""
        results = await self.integrations.enrich_all(self.store.state)
        for provider_name, payload in results.items():
            await self.store.apply_enrichment(provider_name, payload)

    # ── Exécution ─────────────────────────────────────────────────────

    async def run(self) -> None:
        runner = await self.server.start()
        logger.info("Surveillance du dossier : %s", self.journal_dir)
        if not self.journal_dir.exists():
            logger.warning(
                "Dossier journal introuvable — lance Elite Dangerous "
                "ou renseigne ingest.journal_dir dans la config"
            )
        try:
            await self.watcher.start()
        except asyncio.CancelledError:
            pass
        finally:
            self.watcher.stop()
            await runner.cleanup()
