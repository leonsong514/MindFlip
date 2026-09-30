"""Tests for the GitHub Actions workflow file.

The CI workflow lives at ``.github/workflows/ci.yml`` and is loaded
from the repository root. These tests ensure the YAML is well-formed,
the trigger set includes pull requests, and there is no hardcoded
secret in the workflow body.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"


_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{12,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)


def _load_workflow() -> dict:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    assert isinstance(data, dict), "ci.yml must decode to a mapping"
    return data


def test_workflow_yaml_is_parseable() -> None:
    _load_workflow()


def test_workflow_triggers_on_pull_request() -> None:
    data = _load_workflow()
    triggers = data.get(True) or data.get("on")
    assert triggers is not None, "ci.yml must declare triggers under `on:`"
    if isinstance(triggers, str):
        assert triggers == "pull_request"
    else:
        assert "pull_request" in triggers, (
            f"pull_request must be in triggers; got {triggers!r}"
        )


def test_workflow_has_backend_and_frontend_jobs() -> None:
    data = _load_workflow()
    jobs = data.get("jobs") or {}
    assert "backend" in jobs, "ci.yml must define a backend job"
    assert "frontend" in jobs, "ci.yml must define a frontend job"


def test_workflow_uses_minimal_permissions() -> None:
    data = _load_workflow()
    permissions = data.get("permissions")
    assert permissions is not None, "ci.yml must declare permissions"
    assert permissions.get("contents") == "read", (
        "permissions.contents should be 'read' for the minimal default"
    )


def test_workflow_has_no_hardcoded_secret() -> None:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    for pattern in _SECRET_PATTERNS:
        match = pattern.search(text)
        assert match is None, (
            f"ci.yml must not contain pattern {pattern.pattern!r}; "
            f"got {match.group(0)!r}"
        )


def test_backend_job_uses_requirements_lock() -> None:
    data = _load_workflow()
    backend = data["jobs"]["backend"]
    steps_text = yaml.safe_dump(backend)
    assert "requirements.lock" in steps_text, (
        "backend job must install from apps/backend/requirements.lock"
    )


def test_frontend_job_uses_npm_ci() -> None:
    data = _load_workflow()
    frontend = data["jobs"]["frontend"]
    steps_text = yaml.safe_dump(frontend)
    assert "npm ci" in steps_text, "frontend job should use `npm ci`"