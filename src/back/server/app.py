"""Serveur aiohttp — HTTP + WebSocket dans un seul process asyncio.

Routes :
  GET  /              → client web (tablette)
  GET  /api/state     → snapshot complet
  GET  /api/macros    → liste des macros (boutons + config)
  WS   /ws            → bidirectionnel :
                          ← snapshot + diffs d'état (serveur → client)
                          ← macros + mises à jour de raccourcis
                          → exécution de macros
                          → capture / saisie de raccourci (configuration)
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from aiohttp import WSMsgType, web

from back.macros.keyspec import KeySpec

if TYPE_CHECKING:
    from back.core.store import StateStore
    from back.macros.capture import KeyCaptureService
    from back.macros.engine import MacroEngine
    from back.macros.registry import MacroRegistry
    from back.macros.store import KeybindStore

logger = logging.getLogger(__name__)

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


class TerminalServer:
    def __init__(
        self,
        store: StateStore,
        macros: MacroRegistry,
        engine: MacroEngine,
        *,
        capture: KeyCaptureService | None = None,
        keybinds: KeybindStore | None = None,
        host: str = "0.0.0.0",
        port: int = 3300,
    ) -> None:
        self.store = store
        self.macros = macros
        self.engine = engine
        self.capture = capture
        self.keybinds = keybinds
        self.host = host
        self.port = port
        self.app = web.Application()
        self._clients: set[web.WebSocketResponse] = set()
        self._setup_routes()

    def _setup_routes(self) -> None:
        self.app.router.add_get("/api/state", self._handle_state)
        self.app.router.add_get("/api/macros", self._handle_macros)
        self.app.router.add_get("/ws", self._handle_ws)
        self.app.router.add_get("/", self._handle_index)
        if WEB_DIR.exists():
            self.app.router.add_static("/static/", WEB_DIR)

    # ── HTTP ──────────────────────────────────────────────────────────

    async def _handle_index(self, request: web.Request) -> web.StreamResponse:
        index = WEB_DIR / "index.html"
        if index.exists():
            return web.FileResponse(index)
        return web.Response(text="elite_deck — client web absent")

    async def _handle_state(self, request: web.Request) -> web.Response:
        return web.json_response(self.store.snapshot)

    async def _handle_macros(self, request: web.Request) -> web.Response:
        return web.json_response(self.macros.to_client_list())

    # ── WebSocket ─────────────────────────────────────────────────────

    async def _handle_ws(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse(heartbeat=20)
        await ws.prepare(request)
        peer = request.remote
        self._clients.add(ws)
        logger.info("Client WS connecté : %s", peer)

        await ws.send_json({"type": "snapshot", "state": self.store.snapshot})
        await ws.send_json({"type": "macros", "macros": self.macros.to_client_list()})

        queue = self.store.subscribe()
        pusher = asyncio.create_task(self._push_diffs(ws, queue))

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    await self._handle_client_message(ws, msg.json())
                elif msg.type == WSMsgType.ERROR:
                    logger.warning("WS erreur : %s", ws.exception())
        finally:
            pusher.cancel()
            self.store.unsubscribe(queue)
            self._clients.discard(ws)
            logger.info("Client WS déconnecté : %s", peer)
        return ws

    async def _push_diffs(
        self, ws: web.WebSocketResponse, queue: asyncio.Queue[dict[str, Any]]
    ) -> None:
        try:
            while not ws.closed:
                payload = await queue.get()
                await ws.send_json(payload)
        except (ConnectionResetError, asyncio.CancelledError):
            pass

    async def _broadcast(self, payload: dict[str, Any]) -> None:
        for client in list(self._clients):
            if not client.closed:
                try:
                    await client.send_json(payload)
                except ConnectionResetError:
                    self._clients.discard(client)

    # ── Routage des messages client ───────────────────────────────────

    async def _handle_client_message(
        self, ws: web.WebSocketResponse, data: dict[str, Any]
    ) -> None:
        match data.get("type"):
            case "resync":
                await ws.send_json({"type": "snapshot", "state": self.store.snapshot})
            case "macro":
                await self._execute_macro(ws, data.get("id", ""))
            case "capture_start":
                await self._start_capture(ws)
            case "set_keybind":
                await self._set_keybind(ws, data)
            case _:
                pass

    async def _execute_macro(self, ws: web.WebSocketResponse, macro_id: str) -> None:
        macro = self.macros.get(macro_id)
        if macro is None:
            await ws.send_json({"type": "macro_ack", "id": macro_id, "ok": False,
                                "error": "inconnu"})
            return
        if macro.kind == "sequence":
            self.engine.tap_sequence(macro.sequence)
        else:
            self.engine.tap(macro.key)
        logger.info("Macro exécutée : %s", macro_id)
        await ws.send_json({"type": "macro_ack", "id": macro_id, "ok": True})

    async def _start_capture(self, ws: web.WebSocketResponse) -> None:
        if self.capture is None:
            await ws.send_json({"type": "capture_result", "keyspec": None,
                                "error": "capture indisponible"})
            return
        spec = await self.capture.capture(timeout=10.0)
        if spec is None:
            await ws.send_json({"type": "capture_result", "keyspec": None,
                                "error": "aucune touche détectée"})
        else:
            await ws.send_json({"type": "capture_result", "keyspec": spec.to_dict()})

    async def _set_keybind(
        self, ws: web.WebSocketResponse, data: dict[str, Any]
    ) -> None:
        macro_id = data.get("id", "")
        raw = data.get("keyspec")
        if not macro_id or not isinstance(raw, dict):
            await ws.send_json({"type": "keybind_updated", "id": macro_id,
                                "ok": False, "error": "données invalides"})
            return
        spec = KeySpec.from_dict(raw)
        if not self.macros.set_key(macro_id, spec):
            await ws.send_json({"type": "keybind_updated", "id": macro_id,
                                "ok": False, "error": "macro inconnue"})
            return
        if self.keybinds is not None:
            self.keybinds.set(macro_id, spec)
        logger.info("Raccourci mis à jour : %s → %s", macro_id, spec.display())
        # Diffuse à tous les clients pour synchroniser l'affichage
        await self._broadcast({"type": "keybind_updated", "id": macro_id,
                               "ok": True, "keyspec": spec.to_dict()})

    # ── Cycle de vie ──────────────────────────────────────────────────

    async def start(self) -> web.AppRunner:
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info("elite_deck en écoute sur http://%s:%d", self.host, self.port)
        return runner
