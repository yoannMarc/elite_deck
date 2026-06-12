"""Couche d'intégrations externes — point d'extension.

NON IMPLÉMENTÉ pour le moment, mais l'architecture est posée pour brancher
ultérieurement des sources de données externes (EDSM, FDevIDs…) sans modifier
le noyau.

Principe :
  - Chaque provider implémente le ``Protocol`` ``DataProvider``.
  - Le ``IntegrationManager`` orchestre les providers activés et pousse les
    données enrichies dans le ``StateStore`` via ``apply_enrichment``.
  - Tout est asynchrone et optionnel : si aucun provider n'est activé, le cœur
    fonctionne exactement comme aujourd'hui.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Protocol, runtime_checkable

from back.core.models import GameState

logger = logging.getLogger(__name__)


@runtime_checkable
class DataProvider(Protocol):
    """Contrat d'un fournisseur de données externe."""

    name: str
    enabled: bool

    async def enrich(self, state: GameState) -> dict[str, Any]:
        """Retourne un payload d'enrichissement pour l'état courant.

        Doit être idempotent et tolérant aux pannes réseau (retourner ``{}``
        plutôt que lever). Appelé quand un déclencheur pertinent survient
        (ex. changement de système).
        """
        ...


class IntegrationManager:
    """Orchestre les providers activés et alimente le store en enrichissements."""

    def __init__(self, providers: list[DataProvider] | None = None) -> None:
        self.providers: list[DataProvider] = providers or []

    def register(self, provider: DataProvider) -> None:
        self.providers.append(provider)

    @property
    def active(self) -> list[DataProvider]:
        return [p for p in self.providers if getattr(p, "enabled", False)]

    async def enrich_all(self, state: GameState) -> dict[str, dict[str, Any]]:
        """Interroge tous les providers actifs en parallèle.

        Retourne ``{nom_provider: payload}``. Les erreurs sont isolées : un
        provider défaillant n'empêche pas les autres.
        """
        active = self.active
        if not active:
            return {}

        async def _safe(provider: DataProvider) -> tuple[str, dict[str, Any]]:
            try:
                return provider.name, await provider.enrich(state)
            except Exception as exc:
                logger.warning("Provider %s en échec : %s", provider.name, exc)
                return provider.name, {}

        results = await asyncio.gather(*(_safe(p) for p in active))
        return {name: payload for name, payload in results if payload}
