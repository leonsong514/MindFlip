"""SQLAlchemy 2 engine and session factory helpers.

The runtime owns a single engine per process. Tests construct a fresh
engine against a temporary database and dispose it on teardown.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from .paths import default_database_url

PRAGMA_FOREIGN_KEYS = "PRAGMA foreign_keys = ON"
PRAGMA_BUSY_TIMEOUT_MS = "PRAGMA busy_timeout = 5000"


def open_engine(base: Path | None = None) -> Engine:
    """Create a SQLAlchemy engine bound to the application database.

    SQLite-specific options: foreign keys are enabled, a busy timeout
    is set so concurrent readers wait instead of raising immediately.
    The engine is configured for a single-writer desktop app; no
    connection pool tuning is applied.
    """

    url = default_database_url(base)
    engine = create_engine(
        url,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _set_pragmas(dbapi_connection, _connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute(PRAGMA_FOREIGN_KEYS)
            cursor.execute(PRAGMA_BUSY_TIMEOUT_MS)
        finally:
            cursor.close()

    return engine


def open_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def dispose_engine(engine: Engine) -> None:
    engine.dispose()


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""

    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
