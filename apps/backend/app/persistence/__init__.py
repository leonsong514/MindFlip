"""Persistence layer (SQLAlchemy 2 + Alembic).

Iteration 01 only ships a single technical table `storage_probe` used
to verify the migration, close/reopen, and rollback contracts. Domain
models (decisions, criteria, evidence, …) are introduced in later
iterations and must not be imported from this package.
"""

from .paths import default_database_url, resolve_database_path
from .engine import open_engine, open_session_factory, dispose_engine, session_scope
from .migrate import apply_migrations, current_revision

__all__ = [
    "default_database_url",
    "resolve_database_path",
    "open_engine",
    "open_session_factory",
    "dispose_engine",
    "session_scope",
    "apply_migrations",
    "current_revision",
]