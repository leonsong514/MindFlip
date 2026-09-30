"""Tests for the credential boundary (AC8.1, AC8.2, AC8.3).

These tests enforce that:

1. The gitignore pattern blocks local ``.env`` files and the common
   local secret filenames.
2. The committed ``.env.example`` template does not contain any
   plausible API key, token, or PEM block.
3. The committed Python source tree does not contain strings that
   look like real API keys or tokens.

The checks are intentionally heuristic; a positive hit does not
guarantee a leak but a clean run raises the bar for accidental
commits.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout


def test_gitignore_blocks_env_and_local_secrets() -> None:
    pattern_lines = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    patterns = {
        line.strip()
        for line in pattern_lines
        if line.strip() and not line.strip().startswith("#")
    }
    expected = {".env", ".env.*", "**/*.pem", "**/*.key"}
    missing = expected - patterns
    assert not missing, f".gitignore missing expected entries: {missing}"


def test_local_env_in_repo_is_git_ignored() -> None:
    target_dir = REPO_ROOT / ".tmp-credential-test"
    target_dir.mkdir(exist_ok=True)
    try:
        env_file = target_dir / ".env"
        env_file.write_text(
            "MINDFLIP_API_KEY=sk-test-1234567890abcdef\n", encoding="utf-8"
        )
        pem_file = target_dir / "private.pem"
        pem_file.write_text(
            "-----BEGIN PRIVATE KEY-----\nMIIBV\n-----END PRIVATE KEY-----\n",
            encoding="utf-8",
        )
        key_file = target_dir / "id.key"
        key_file.write_text("placeholder\n", encoding="utf-8")

        key_status = _run_git(["check-ignore", "-v", str(env_file)]).strip()
        pem_status = _run_git(["check-ignore", "-v", str(pem_file)]).strip()
        raw_status = _run_git(["check-ignore", "-v", str(key_file)]).strip()

        assert key_status, ".env should be ignored"
        assert pem_status, "private.pem should be ignored"
        assert raw_status, "id.key should be ignored"
    finally:
        for child in target_dir.iterdir():
            child.unlink()
        target_dir.rmdir()


def test_env_example_is_tracked() -> None:
    result = subprocess.run(
        ["git", "check-ignore", "-v", "--", ".env.example"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0, (
        ".env.example must NOT be ignored by any positive rule; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )

    listed = _run_git(["ls-files", "--error-unmatch", ".env.example"]).strip()
    assert ".env.example" in listed, ".env.example should be tracked"


_KEY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{12,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
)


def test_env_example_has_no_real_secret() -> None:
    text = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
    for pattern in _KEY_PATTERNS:
        match = pattern.search(text)
        assert match is None, (
            f".env.example must not contain pattern {pattern.pattern!r}; "
            f"got {match.group(0)!r}"
        )


def test_python_source_has_no_real_secret() -> None:
    offenders: list[tuple[str, str]] = []
    for path in (REPO_ROOT / "apps" / "backend" / "app").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for pattern in _KEY_PATTERNS:
            match = pattern.search(text)
            if match is not None:
                offenders.append((str(path), match.group(0)))
    assert not offenders, f"Potential secrets in Python sources: {offenders}"


def test_config_loader_does_not_log_secrets() -> None:
    """The configuration loader must not print or log secrets."""

    import ast

    text = (REPO_ROOT / "apps" / "backend" / "app" / "config.py").read_text(
        encoding="utf-8"
    )
    assert "print(" not in text, "config.py must not print() values"
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != "logging", "config.py must not import logging"
        elif isinstance(node, ast.ImportFrom):
            assert node.module != "logging", "config.py must not import logging"


def test_db_layer_has_no_secret_persistence() -> None:
    """Persistence layer must not write API key-like columns.

    The persistence package owns SQLite access for the runtime. A
    scan against column names and CREATE TABLE statements keeps the
    architecture rule visible in tests.
    """

    forbidden_substrings = (
        "api_key",
        "api-key",
        "secret",
        "token",
        "password",
    )
    for path in (REPO_ROOT / "apps" / "backend" / "app" / "persistence").rglob("*.py"):
        content = path.read_text(encoding="utf-8").lower()
        for term in forbidden_substrings:
            assert term not in content, (
                f"{path} mentions forbidden term {term!r}; secrets must not be persisted"
            )
