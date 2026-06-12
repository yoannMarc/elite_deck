"""Provider EDSM — https://www.edsm.net/en/api-v1

STATUT : STUB. Architecture prête, implémentation différée.

EDSM expose des informations sur les systèmes stellaires (corps, stations,
trafic, valeur d'exploration…). L'idée : quand le commandant change de système,
on interroge EDSM pour enrichir l'affichage (ex. nombre de corps, stations
connues, valeur estimée).

Pour activer plus tard :
  1. Passer ``enabled=True``.
  2. Implémenter ``enrich`` avec un appel HTTP (aiohttp.ClientSession partagée).
  3. Respecter le rate limiting et le cache (EDSM demande de ne pas marteler
     l'API ; mettre en cache par nom de système).

Endpoints utiles (api-v1) :
  - GET /api-v1/system?systemName=<nom>&showCoordinates=1&showInformation=1
  - GET /api-system-v1/bodies?systemName=<nom>
  - GET /api-system-v1/stations?systemName=<nom>
"""

from __future__ import annotations

from typing import Any

from back.core.models import GameState

EDSM_BASE_URL = "https://www.edsm.net"


class EDSMProvider:
    """Fournisseur EDSM (stub)."""

    name = "edsm"

    def __init__(self, *, enabled: bool = False, timeout: float = 5.0) -> None:
        self.enabled = enabled
        self.timeout = timeout
        self._cache: dict[str, dict[str, Any]] = {}  # systemName -> payload

    async def enrich(self, state: GameState) -> dict[str, Any]:
        """Enrichit avec les données du système courant.

        STUB : retourne ``{}``. L'implémentation réelle ferait :

            system = state.navigation.system
            if not system or system in self._cache:
                return self._cache.get(system, {})
            async with aiohttp.ClientSession() as s:
                url = f"{EDSM_BASE_URL}/api-v1/system"
                params = {"systemName": system, "showInformation": 1,
                          "showCoordinates": 1}
                async with s.get(url, params=params, timeout=self.timeout) as r:
                    data = await r.json()
            payload = {"bodies": ..., "stations": ..., "info": data}
            self._cache[system] = payload
            return payload
        """
        return {}
