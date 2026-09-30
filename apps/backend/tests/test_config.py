"""Unit tests for the local configuration loader.

The loader is the boundary between plain environment variables and
the runtime defaults. Tests inject temporary ``.env`` files and
clear the relevant environment variables to exercise resolution
order without touching the real user environment.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config import defaults, load_config
from app.persistence.paths import default_database_url, user_data_dir


def test_defaults_returns_python_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MINDFLIP_PYTHON", raising=False)
    monkeypatch.delenv("MINDFLIP_DATA_DIR", raising=False)
    monkeypatch.delenv("MINDFLIP_DB_URL", raising=False)
    cfg = defaults()
    assert cfg.python_executable == "python"
    assert cfg.data_dir is None
    assert cfg.db_url is None


def test_env_file_overrides_defaults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MINDFLIP_PYTHON", raising=False)
    monkeypatch.delenv("MINDFLIP_DATA_DIR", raising=False)
    monkeypatch.delenv("MINDFLIP_DB_URL", raising=False)
    monkeypatch.chdir(tmp_path)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "# header comment",
                "MINDFLIP_PYTHON=/usr/bin/python3",
                'MINDFLIP_DATA_DIR="C:\\\\Users\\\\me\\\\AppData\\\\Roaming\\\\MindFlip"',
                "",
                "MINDFLIP_DB_URL=sqlite:///tmp/foo.db",
            ]
        ),
        encoding="utf-8",
    )

    cfg = load_config()

    assert cfg.python_executable == "/usr/bin/python3"
    assert cfg.data_dir == Path("C:\\Users\\me\\AppData\\Roaming\\MindFlip")
    assert cfg.db_url == "sqlite:///tmp/foo.db"


def test_environment_variable_overrides_env_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("MINDFLIP_PYTHON=/from/file\n", encoding="utf-8")
    monkeypatch.setenv("MINDFLIP_PYTHON", "/from/env")

    cfg = load_config()
    assert cfg.python_executable == "/from/env"


def test_env_file_ignores_comments_and_blanks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MINDFLIP_PYTHON", raising=False)
    monkeypatch.delenv("MINDFLIP_DATA_DIR", raising=False)
    monkeypatch.delenv("MINDFLIP_DB_URL", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "# this is a comment",
                "",
                "MINDFLIP_PYTHON=/usr/bin/python3",
                "INVALID_LINE_WITHOUT_EQUALS",
            ]
        ),
        encoding="utf-8",
    )

    cfg = load_config()
    assert cfg.python_executable == "/usr/bin/python3"


def test_quoted_values_are_unwrapped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MINDFLIP_PYTHON", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "MINDFLIP_PYTHON='/usr/bin/python3'\n", encoding="utf-8"
    )

    cfg = load_config()
    assert cfg.python_executable == "/usr/bin/python3"


def test_missing_env_file_falls_back_to_defaults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MINDFLIP_PYTHON", raising=False)
    monkeypatch.delenv("MINDFLIP_DATA_DIR", raising=False)
    monkeypatch.delenv("MINDFLIP_DB_URL", raising=False)
    monkeypatch.chdir(tmp_path)

    cfg = load_config()
    assert cfg.python_executable == "python"
    assert cfg.data_dir is None
    assert cfg.db_url is None


def test_env_file_does_not_load_when_empty_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MINDFLIP_PYTHON", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("=orphan\n", encoding="utf-8")

    cfg = load_config()
    assert cfg.python_executable == "python"


def test_env_file_data_dir_reaches_persistence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MINDFLIP_DATA_DIR", raising=False)
    monkeypatch.delenv("MINDFLIP_DB_URL", raising=False)
    monkeypatch.chdir(tmp_path)
    data_dir = tmp_path / "mindflip-data"
    (tmp_path / ".env").write_text(f"MINDFLIP_DATA_DIR={data_dir}\n", encoding="utf-8")

    assert user_data_dir() == data_dir
    assert (
        default_database_url()
        == f"sqlite:///{(data_dir / 'database' / 'app.db').as_posix()}"
    )


def test_env_file_db_url_reaches_persistence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MINDFLIP_DB_URL", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "MINDFLIP_DB_URL=sqlite:///custom.db\n", encoding="utf-8"
    )

    assert default_database_url() == "sqlite:///custom.db"
    assert default_database_url(tmp_path) != "sqlite:///custom.db"
