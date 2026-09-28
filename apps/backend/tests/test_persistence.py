"""Persistence integration tests.

These tests exercise the full persistence contract defined in the
iteration 01 testing & acceptance document:

- alembic upgrade creates the schema and records the version
- insert + commit + close + reopen + query preserves the value
- repeated upgrade on an existing database does NOT rebuild the
  schema or drop rows
- a failed transaction rolls back without producing half-committed
  data
- the health service remains independent of the database
"""

from __future__ import annotations

import os
import json
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import text

from app import __version__
from app.api import health_status
from app.persistence import (
    apply_migrations,
    current_revision,
    default_database_url,
    dispose_engine,
    open_engine,
    open_session_factory,
    session_scope,
)
from app.persistence.models import StorageProbe


@pytest.fixture()
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    base = tmp_path / "data"
    base.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("MINDFLIP_DATA_DIR", str(base))
    return base


def test_resolve_database_path_creates_parent(data_dir: Path) -> None:
    db_path = data_dir / "database" / "app.db"
    assert not db_path.exists()
    from app.persistence.paths import resolve_database_path

    resolved = resolve_database_path(data_dir)
    assert resolved == db_path
    assert resolved.parent.is_dir()


def test_apply_migrations_records_version(data_dir: Path) -> None:
    url = apply_migrations(data_dir)
    assert url == default_database_url(data_dir)
    assert current_revision(data_dir) == "0001_initial"

    engine = open_engine(data_dir)
    try:
        with engine.connect() as connection:
            rows = connection.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            ).all()
        table_names = {row[0] for row in rows}
        assert "storage_probe" in table_names
        assert "alembic_version" in table_names
    finally:
        dispose_engine(engine)


def test_cli_init_db_upgrades_fresh_database(data_dir: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "app", "--init-db"],
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
        timeout=10,
        env={**os.environ, "MINDFLIP_DATA_DIR": str(data_dir)},
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["revision"] == "0001_initial"
    assert current_revision(data_dir) == "0001_initial"


def test_insert_commit_reopen_preserves_value(data_dir: Path) -> None:
    apply_migrations(data_dir)

    engine = open_engine(data_dir)
    try:
        factory = open_session_factory(engine)
        with session_scope(factory) as session:
            session.add(StorageProbe(value="hello"))
    finally:
        dispose_engine(engine)

    engine2 = open_engine(data_dir)
    try:
        factory2 = open_session_factory(engine2)
        with session_scope(factory2) as session:
            rows = session.query(StorageProbe).all()
        assert [row.value for row in rows] == ["hello"]
    finally:
        dispose_engine(engine2)


def test_repeated_upgrade_does_not_drop_rows(data_dir: Path) -> None:
    apply_migrations(data_dir)
    engine = open_engine(data_dir)
    try:
        factory = open_session_factory(engine)
        with session_scope(factory) as session:
            session.add(StorageProbe(value="first"))
            session.add(StorageProbe(value="second"))
    finally:
        dispose_engine(engine)

    apply_migrations(data_dir)

    engine3 = open_engine(data_dir)
    try:
        factory3 = open_session_factory(engine3)
        with session_scope(factory3) as session:
            values = [row.value for row in session.query(StorageProbe).all()]
        assert sorted(values) == ["first", "second"]
    finally:
        dispose_engine(engine3)


def test_failed_transaction_rolls_back(data_dir: Path) -> None:
    apply_migrations(data_dir)
    engine = open_engine(data_dir)
    try:
        factory = open_session_factory(engine)
        session = factory()
        try:
            session.add(StorageProbe(value="doomed"))
            session.flush()
            # Simulate a downstream failure before commit.
            raise RuntimeError("simulated downstream failure")
        except RuntimeError:
            session.rollback()
        finally:
            session.close()
    finally:
        dispose_engine(engine)

    engine2 = open_engine(data_dir)
    try:
        with engine2.connect() as connection:
            count = connection.execute(
                text("SELECT COUNT(*) FROM storage_probe")
            ).scalar_one()
        assert count == 0
    finally:
        dispose_engine(engine2)


def test_session_scope_rolls_back_on_exception(data_dir: Path) -> None:
    apply_migrations(data_dir)
    engine = open_engine(data_dir)
    try:
        factory = open_session_factory(engine)
        with pytest.raises(RuntimeError, match="boom"):
            with session_scope(factory) as session:
                session.add(StorageProbe(value="rolled-back"))
                raise RuntimeError("boom")
    finally:
        dispose_engine(engine)

    engine2 = open_engine(data_dir)
    try:
        with engine2.connect() as connection:
            count = connection.execute(
                text("SELECT COUNT(*) FROM storage_probe")
            ).scalar_one()
        assert count == 0
    finally:
        dispose_engine(engine2)


def test_unwritable_directory_raises_diagnosable_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog
) -> None:
    if sys.platform.startswith("win"):
        pytest.skip("read-only directory semantics differ on Windows for tests")
    target = tmp_path / "locked"
    target.mkdir()
    os.chmod(target, 0o500)
    monkeypatch.setenv("MINDFLIP_DATA_DIR", str(target))
    with pytest.raises(Exception):
        from app.persistence.paths import resolve_database_path

        resolve_database_path()


def test_health_service_remains_db_independent() -> None:
    """The health probe must not import the persistence layer.

    This guards the architecture rule: health is a runtime check, not
    a database check.
    """

    src = Path(health_status.__code__.co_filename).read_text(encoding="utf-8")
    assert "persistence" not in src.lower()
    assert "sqlalchemy" not in src.lower()
    # Smoke check: the probe still produces a version-stamped OK.
    result = health_status(__version__)
    assert result.status == "ok"
    assert result.version == __version__
