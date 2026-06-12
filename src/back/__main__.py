"""Point d'entrée — ``python -m elite_deck``."""

from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from back.app import Application
from back.config import AppConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="elite_deck",
        description="Terminal + macros Elite Dangerous (second écran tablette)",
    )
    parser.add_argument("-c", "--config", type=Path, default=None,
                        help="Fichier de config TOML")
    parser.add_argument("--journal-dir", type=Path, default=None,
                        help="Dossier des logs ED (surcharge la config)")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--no-replay", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> AppConfig:
    config = AppConfig.load(args.config)
    if args.journal_dir is not None:
        config.ingest.journal_dir = str(args.journal_dir)
    if args.host is not None:
        config.server.host = args.host
    if args.port is not None:
        config.server.port = args.port
    if args.no_replay:
        config.ingest.replay_history = False
    return config


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )
    config = build_config(args)
    app = Application(config)
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        logging.getLogger("elite_deck").info("Arrêt.")


if __name__ == "__main__":
    main()
