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

from app import __version__
from app.api import health_payload

PROTOCOL_VERSION = 1


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
    if raw.get("protocol_version") != PROTOCOL_VERSION:
        raise ProtocolError(
            "invalid_protocol",
            f"unsupported protocol_version: {raw.get('protocol_version')!r}",
        )
    request_id = raw.get("request_id")
    if not isinstance(request_id, str) or not request_id:
        raise ProtocolError("invalid_protocol", "request_id must be a non-empty string")
    method = raw.get("method")
    if not isinstance(method, str) or not method:
        raise ProtocolError("invalid_protocol", "method must be a non-empty string")
    params = raw.get("params", {})
    if not isinstance(params, dict):
        raise ProtocolError("invalid_protocol", "params must be an object")
    return Request(
        protocol_version=PROTOCOL_VERSION,
        request_id=request_id,
        method=method,
        params=params,
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
    return {
        "protocol_version": PROTOCOL_VERSION,
        "request_id": request.request_id,
        "ok": True,
        "result": result,
    }


def build_error_response(request_id: str, code: str, message: str) -> dict:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "request_id": request_id,
        "ok": False,
        "error": {"code": code, "message": message},
    }


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