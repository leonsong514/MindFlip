"""Integration tests for the stdio IPC engine.

These tests exercise the envelope parse/dispatch logic and the
end-to-end behaviour of `python -m app.api.ipc` over a real pipe.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from app import __version__
from app.api import (
    PROTOCOL_VERSION,
    ProtocolError,
    build_error_response,
    build_success_response,
    dispatch,
    handle_line,
    parse_request,
)


REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_ipc(stdin_text: str, timeout: float = 5.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "app.ipc_main"],
        cwd=REPO_ROOT,
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def test_parse_request_health() -> None:
    request = parse_request(
        '{"protocol_version":1,"request_id":"r-001","method":"health/check","params":{}}'
    )
    assert request.protocol_version == PROTOCOL_VERSION
    assert request.request_id == "r-001"
    assert request.method == "health/check"
    assert request.params == {}


def test_parse_request_rejects_missing_version() -> None:
    with pytest.raises(ProtocolError) as exc:
        parse_request('{"request_id":"r-1","method":"health/check"}')
    assert exc.value.code == "invalid_protocol"


def test_parse_request_rejects_unknown_method() -> None:
    request = parse_request(
        '{"protocol_version":1,"request_id":"r-1","method":"nope/x"}'
    )
    with pytest.raises(ProtocolError) as exc:
        dispatch(request)
    assert exc.value.code == "unknown_method"


def test_handle_line_success() -> None:
    response = handle_line(
        '{"protocol_version":1,"request_id":"r-ok","method":"health/check","params":{}}'
    )
    assert response["ok"] is True
    assert response["request_id"] == "r-ok"
    assert response["result"]["status"] == "ok"
    assert response["result"]["version"] == __version__


def test_handle_line_invalid_json_yields_invalid_protocol() -> None:
    response = handle_line("not json")
    assert response["ok"] is False
    assert response["error"]["code"] == "invalid_protocol"
    assert response["request_id"] == ""


def test_handle_line_echoes_request_id_on_unknown_method() -> None:
    response = handle_line(
        '{"protocol_version":1,"request_id":"r-unknown","method":"nope/x","params":{}}'
    )
    assert response["ok"] is False
    assert response["error"]["code"] == "unknown_method"
    assert response["request_id"] == "r-unknown"


def test_build_error_response_shape() -> None:
    response = build_error_response("r-1", "timeout", "no reply in 3s")
    assert response == {
        "protocol_version": 1,
        "request_id": "r-1",
        "ok": False,
        "error": {"code": "timeout", "message": "no reply in 3s"},
    }


def test_build_success_response_shape() -> None:
    class _StubRequest:
        request_id = "r-1"

    response = build_success_response(_StubRequest(), {"status": "ok"})
    assert response == {
        "protocol_version": 1,
        "request_id": "r-1",
        "ok": True,
        "result": {"status": "ok"},
    }


def test_subprocess_round_trip_health() -> None:
    proc = _run_ipc(
        '{"protocol_version":1,"request_id":"r-001","method":"health/check","params":{}}\n'
    )
    assert proc.returncode == 0
    assert proc.stderr == ""
    line = proc.stdout.strip()
    payload = json.loads(line)
    assert payload["ok"] is True
    assert payload["request_id"] == "r-001"
    assert payload["result"]["status"] == "ok"


def test_subprocess_round_trip_unknown_method() -> None:
    proc = _run_ipc(
        '{"protocol_version":1,"request_id":"r-2","method":"nope/x","params":{}}\n'
    )
    assert proc.returncode == 0
    payload = json.loads(proc.stdout.strip())
    assert payload["ok"] is False
    assert payload["error"]["code"] == "unknown_method"
    assert payload["request_id"] == "r-2"


def test_subprocess_round_trip_invalid_protocol() -> None:
    proc = _run_ipc("not json\n")
    assert proc.returncode == 0
    payload = json.loads(proc.stdout.strip())
    assert payload["ok"] is False
    assert payload["error"]["code"] == "invalid_protocol"