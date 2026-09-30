"""IPC engine: stdio JSON Lines request/response over one request.

The runtime reads exactly one envelope line from stdin, dispatches it
to a registered method, writes exactly one envelope response to
stdout, and exits. Diagnostics are written to stderr only.

The engine is intentionally synchronous and short-lived. The Tauri
host owns the process lifecycle; it spawns this engine per request
and recycles the process on errors. This keeps state simple and
makes timeouts and error mapping deterministic.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Callable, Mapping

from pydantic import ValidationError

from app import __version__
from app.api import health_payload
from app.api.contracts import (
    PROTOCOL_VERSION,
    HealthFailure,
    HealthRequest,
    HealthSuccess,
)

PROTOCOL_VERSION = PROTOCOL_VERSION


class ProtocolError(Exception):
    """Raised when a request or response envelope is malformed."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class Request:
    protocol_version: int
    request_id: str
    method: str
    params: dict


def parse_request(line: str) -> Request:
    if not line.strip():
        raise ProtocolError("invalid_protocol", "empty request line")
    try:
        raw = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ProtocolError("invalid_protocol", f"not valid json: {exc.msg}") from exc
    if not isinstance(raw, dict):
        raise ProtocolError("invalid_protocol", "request must be a json object")
    try:
        request = HealthRequest.model_validate(raw)
    except ValidationError as exc:
        raise ProtocolError(
            "invalid_protocol",
            f"request envelope failed validation: {exc.error_count()} error(s)",
        ) from exc
    return Request(
        protocol_version=PROTOCOL_VERSION,
        request_id=request.request_id,
        method=request.method,
        params=dict(request.params),
    )


def _method_health(_: dict) -> dict:
    return health_payload(__version__)


METHODS: Mapping[str, Callable[[dict], dict]] = {
    "health/check": _method_health,
}


def dispatch(request: Request) -> dict:
    handler = METHODS.get(request.method)
    if handler is None:
        raise ProtocolError("unknown_method", f"unknown method: {request.method}")
    return handler(request.params)


def build_success_response(request: Request, result: dict) -> dict:
    envelope = HealthSuccess(
        protocol_version=PROTOCOL_VERSION,
        request_id=request.request_id,
        ok=True,
        result=result,
    )
    return json.loads(envelope.model_dump_json())


def build_error_response(request_id: str, code: str, message: str) -> dict:
    envelope = HealthFailure.model_validate(
        {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": request_id,
            "ok": False,
            "error": {"code": code, "message": message},
        }
    )
    return json.loads(envelope.model_dump_json())


def _emit(response: dict) -> None:
    json.dump(response, sys.stdout, ensure_ascii=False, separators=(",", ":"))
    sys.stdout.write("\n")
    sys.stdout.flush()


def handle_line(line: str) -> dict:
    """Parse, dispatch, and format a response for a single request line.

    Returns the response dict without writing to stdout. Useful for
    tests and for callers that want to inspect the response.
    """

    try:
        request = parse_request(line)
    except ProtocolError as exc:
        # Best effort: request_id may be absent or invalid; we still
        # attempt to extract a string for the envelope.
        request_id = ""
        try:
            raw = json.loads(line) if line.strip() else {}
            candidate = raw.get("request_id") if isinstance(raw, dict) else None
            if isinstance(candidate, str):
                request_id = candidate
        except json.JSONDecodeError:
            pass
        return build_error_response(request_id, exc.code, exc.message)
    try:
        result = dispatch(request)
    except ProtocolError as exc:
        return build_error_response(request.request_id, exc.code, exc.message)
    return build_success_response(request, result)


def serve_stdio() -> int:
    """Read one line from stdin, write one response line to stdout."""

    line = sys.stdin.readline()
    response = handle_line(line)
    _emit(response)
    return 0 if response.get("ok") else 0
