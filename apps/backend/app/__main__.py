"""Command-line entrypoint for the Python Agent Runtime.

Iteration 01 only exposes a deterministic health probe. The transport
layer (stdio JSON Lines IPC to Tauri) is added in task 3 and reads
from this entrypoint.
"""

from __future__ import annotations

import argparse
import json
import sys

from app import __version__
from app.api import health_payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mindflip-backend",
        description="MindFlip Python Agent Runtime (iteration 01)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"mindflip-backend {__version__}",
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Print a single health probe response as JSON and exit.",
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Upgrade the local SQLite database to the latest migration.",
    )
    return parser


def run_health() -> int:
    payload = health_payload(__version__)
    json.dump(payload, sys.stdout, ensure_ascii=False, separators=(",", ":"))
    sys.stdout.write("\n")
    sys.stdout.flush()
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.health:
        return run_health()
    if args.init_db:
        from app.persistence import apply_migrations, current_revision

        apply_migrations()
        json.dump(
            {"status": "ready", "revision": current_revision()},
            sys.stdout,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        sys.stdout.write("\n")
        return 0
    build_parser().print_help(sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
