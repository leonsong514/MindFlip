"""Local configuration loader.

Iteration 02 introduces a minimal configuration boundary. Plain
configuration values (paths, log levels, feature flags that are not
secrets) flow through this module. Sensitive credentials are NOT
loaded here; the future OS credential bridge owns those values.

Resolution order (highest priority first):

1. Process environment variables.
2. ``.env`` file in the repository root or ``apps/backend``.
3. Compiled-in defaults returned by ``defaults()``.

The loader is intentionally tiny. It does not implement dotenv
parsing: the few keys it understands are simple ``KEY=VALUE`` lines.
Comments and blank lines are tolerated. Quoted values are stripped
of their surrounding quotes.

API keys and similar secrets must never appear in a committed file.
The gitignore already excludes ``.env``, ``.env.*`` and local secret
files; the architecture baseline forbids persisting them to SQLite
or logging them.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ENV_FILE_CANDIDATES: tuple[Path, ...] = (
    Path(".env"),
    Path("apps/backend/.env"),
)


@dataclass(frozen=True)
class Config:
    python_executable: str
    data_dir: Path | None
    db_url: str | None


def defaults() -> Config:
    return Config(
        python_executable=os.environ.get("MINDFLIP_PYTHON", "python"),
        data_dir=None,
        db_url=None,
    )


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[key] = value
    return values


def _collect_file_values() -> dict[str, str]:
    merged: dict[str, str] = {}
    for candidate in ENV_FILE_CANDIDATES:
        merged.update(_read_env_file(candidate))
    return merged


def load_config() -> Config:
    file_values = _collect_file_values()

    def pick(key: str, default: str | None = None) -> str | None:
        if key in os.environ:
            return os.environ[key]
        if key in file_values:
            return file_values[key]
        return default

    data_dir_raw = pick("MINDFLIP_DATA_DIR")
    data_dir = Path(data_dir_raw) if data_dir_raw else None
    return Config(
        python_executable=pick("MINDFLIP_PYTHON", "python") or "python",
        data_dir=data_dir,
        db_url=pick("MINDFLIP_DB_URL"),
    )
