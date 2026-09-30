"""Run Alembic migrations to the latest revision.

Tests invoke ``apply_migrations(base)`` against a temporary data
directory. The runtime is also expected to call this on startup
(task 4 integration point; iteration 01 exposes it as a Python API
and the tests exercise it directly).
"""

from __future__ import annotations

import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from .paths import default_database_url

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"
MIGRATIONS_DIR = BACKEND_ROOT / "migrations"


def _build_config(url: str) -> Config:
    # Load alembic.ini so its [alembic] section (version_table,
    # version_table_pk, log config, etc.) is honoured. The script
    # location and sqlalchemy.url are then overridden per call.
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", url)
    # env.py imports the application package (``app.persistence...``),
    # so we must put the backend root on sys.path regardless of CWD.
    if str(BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(BACKEND_ROOT))
    return config


def apply_migrations(base: Path | None = None) -> str:
    """Apply all pending migrations to the database at ``base``."""

    url = default_database_url(base)
    config = _build_config(url)
    command.upgrade(config, "head")
    return url


def current_revision(base: Path | None = None) -> str | None:
    """Return the current Alembic revision, or ``None`` if uninitialised.

    Reads the ``alembic_version`` table directly instead of relying on
    ``alembic.command.current``, whose return value is not part of the
    public API and only emits to stdout as a side effect.
    """

    from .engine import dispose_engine, open_engine

    engine = open_engine(base)
    try:
        with engine.connect() as connection:
            rows = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).all()
        if not rows:
            return None
        return rows[0][0]
    finally:
        dispose_engine(engine)
