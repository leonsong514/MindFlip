"""Health service unit tests.

The probe must return a deterministic OK payload on every call, must
not depend on the database, and must be safe to invoke from any
working directory.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from app import __version__
from app.api import health_payload, health_status


def test_health_status_is_ok() -> None:
    result = health_status(__version__)
    assert result.status == "ok"
    assert result.version == __version__
    assert result.timestamp.endswith("+00:00") or result.timestamp.endswith("Z")


def test_health_status_is_deterministic_in_shape() -> None:
    first = health_payload(__version__)
    second = health_payload(__version__)
    assert set(first) == set(second) == {"status", "version", "timestamp"}
    assert first["status"] == second["status"] == "ok"
    assert first["version"] == second["version"] == __version__


def test_health_does_not_require_database(monkeypatch: pytest.MonkeyPatch) -> None:
    """The probe must not import SQLAlchemy or alembic.

    Guards against accidentally wiring database imports into the
    health path during future refactors.
    """

    import app.api.health as health_module

    src = Path(health_module.__file__).read_text(encoding="utf-8")
    assert "sqlalchemy" not in src.lower()
    assert "alembic" not in src.lower()


def test_cli_health_emits_single_line_json() -> None:
    """`python -m app --health` prints a single line of JSON to stdout."""

    repo_root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "app", "--health"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["status"] == "ok"
    assert payload["version"] == __version__