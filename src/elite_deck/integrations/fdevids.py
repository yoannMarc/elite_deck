"""Provider FDevIDs — https://github.com/EDCD/FDevIDs

STATUT : STUB. Architecture prête, implémentation différée.

FDevIDs n'est pas une bibliothèque pip mais un dépôt de fichiers CSV maintenus
par l'EDCD, qui font la correspondance entre les identifiants internes du jeu
(ex. ``cobramkiii``) et des noms lisibles (ex. ``Cobra MkIII``), pour les
vaisseaux, modules, marchandises, etc.

Usage prévu : résoudre ``ship.type`` → ``ship.type_label``, traduire les noms
de marchandises du cargo, etc. — purement local après téléchargement des CSV.

Pour activer plus tard :
  1. Télécharger/embarquer les CSV (shipyard.csv, commodity.csv, modules.csv…)
     depuis le dépôt EDCD/FDevIDs, idéalement mis en cache localement.
  2. Charger les CSV en dictionnaires au démarrage (``csv`` stdlib).
  3. Passer ``enabled=True`` et implémenter ``resolve_*`` / ``enrich``.

Contrairement à EDSM, c'est de la donnée statique locale : pas de rate limiting,
pas de réseau au runtime une fois les CSV récupérés.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from elite_deck.core.models import GameState

# URL de référence des CSV (téléchargement à prévoir lors de l'implémentation)
FDEVIDS_REPO = "https://github.com/EDCD/FDevIDs"


class FDevIDsProvider:
    """Résolveur d'identifiants internes → noms lisibles (stub)."""

    name = "fdevids"

    def __init__(self, *, enabled: bool = False, data_dir: Path | None = None) -> None:
        self.enabled = enabled
        self.data_dir = data_dir
        self._ships: dict[str, str] = {}       # cobramkiii -> Cobra MkIII
        self._commodities: dict[str, str] = {}  # tritium -> Tritium
        # self._load_csv()  # à appeler quand les CSV sont disponibles

    def resolve_ship(self, internal: str) -> str:
        """Retourne le nom lisible d'un vaisseau, ou l'identifiant brut."""
        return self._ships.get(internal.lower(), internal)

    def resolve_commodity(self, internal: str) -> str:
        return self._commodities.get(internal.lower(), internal)

    async def enrich(self, state: GameState) -> dict[str, Any]:
        """STUB : retourne ``{}``.

        L'implémentation remplirait ``ship.type_label`` et traduirait les noms
        du cargo via les tables CSV chargées en mémoire.
        """
        return {}
