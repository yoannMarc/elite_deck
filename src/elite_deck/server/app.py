"""Serveur aiohttp — HTTP + WebSocket dans un seul process asyncio.

Routes :
  GET  /              → client web (tablette)
  GET  /api/state     → snapshot complet
  GET  /api/macros    → liste des macros (pour dessiner les boutons)
  WS   /ws            → bidirectionnel :
                          ← snapshot + diffs d'état (serveur → client)
                          → exécution de macros (client → serveur)
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from aiohttp import WSMsgType, web

from elite_deck.core.store import StateStore
from elite_deck.macros.engine import MacroEngine
from elite_deck.macros.registry import MacroRegistry

logger = logging.getLogger(__name__)

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


class TerminalServer:
    def __init__(
        self,
        store: StateStore,
        macros: MacroRegistry,
        engine: MacroEngine,
        *,
        host: str = "0.0.0.0",
        port: int = 3300,
    ) -> None:
        self.store = store
        self.macros = macros
        self.engine = engine
        self.host = host
        self.port = port
        self.app = web.Application()
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
        logger.info("Client WS connecté : %s", peer)

        # Snapshot initial + liste des macros
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

    async def _handle_client_message(
        self, ws: web.WebSocketResponse, data: dict[str, Any]
    ) -> None:
        msg_type = data.get("type")

        if msg_type == "resync":
            await ws.send_json({"type": "snapshot", "state": self.store.snapshot})

        elif msg_type == "macro":
            macro_id = data.get("id", "")
            await self._execute_macro(ws, macro_id)

    async def _execute_macro(self, ws: web.WebSocketResponse, macro_id: str) -> None:
        macro = self.macros.get(macro_id)
        if macro is None:
            await ws.send_json({"type": "macro_ack", "id": macro_id, "ok": False,
                                "error": "inconnu"})
            return
        if macro.kind == "sequence":
            self.engine.send_sequence(macro.sequence)
        else:
            self.engine.send(macro.keybind)
        logger.info("Macro exécutée : %s", macro_id)
        await ws.send_json({"type": "macro_ack", "id": macro_id, "ok": True})

    # ── Cycle de vie ──────────────────────────────────────────────────

    async def start(self) -> web.AppRunner:
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info("elite_deck en écoute sur http://%s:%d", self.host, self.port)
        return runner
