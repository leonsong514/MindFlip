"""Application data directory resolution.

The runtime stores its SQLite database under the user's per-application
data directory. Tests inject a temporary path via the
``MINDFLIP_DATA_DIR`` environment variable so they never touch the
real user profile.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from app.config import load_config

APP_DIR_NAME = "MindFlip"
DATABASE_DIR = "database"
DATABASE_FILE = "app.db"


def user_data_dir() -> Path:
    """Return the per-user data directory for the application.

    Resolution rules (Windows is the supported MVP target):
    - Honour ``MINDFLIP_DATA_DIR`` if set (used by tests and overrides).
    - Otherwise read ``%APPDATA%`` (Windows) or fall back to the
      platform default (``~/.local/share`` on Linux, ``~/Library/Application
      Support`` on macOS). The repository never commits anything under
      this directory.
    """

    override = load_config().data_dir
    if override is not None:
        return override

    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / APP_DIR_NAME
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_DIR_NAME

    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / APP_DIR_NAME


def resolve_database_path(base: Path | None = None) -> Path:
    """Return the SQLite database path, ensuring the parent exists.

    A missing parent directory is created. The function never creates
    the database file itself; that is the engine/migration step's
    responsibility.
    """

    root = base if base is not None else user_data_dir()
    db_dir = root / DATABASE_DIR
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / DATABASE_FILE


def default_database_url(base: Path | None = None) -> str:
    """Build a SQLAlchemy URL for the resolved SQLite path."""

    if base is None:
        override = load_config().db_url
        if override:
            return override
    path = resolve_database_path(base)
    return f"sqlite:///{path.as_posix()}"
