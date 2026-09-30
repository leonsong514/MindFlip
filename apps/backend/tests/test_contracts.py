"""Pydantic boundary model unit tests.

These tests exercise the validation rules of ``app.api.contracts``
independent of the IPC engine. The IPC engine already uses these
models; this file documents the wire-level contract that both the
Python runtime and the Rust host depend on.
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from app.api.contracts import (
    KNOWN_METHODS,
    PROTOCOL_VERSION,
    HealthErrorBody,
    HealthFailure,
    HealthRequest,
    HealthResult,
    HealthSuccess,
)


def test_health_request_minimal() -> None:
    request = HealthRequest.model_validate(
        {
            "protocol_version": 1,
            "request_id": "r-1",
            "method": "health/check",
        }
    )
    assert request.protocol_version == PROTOCOL_VERSION
    assert request.request_id == "r-1"
    assert request.method == "health/check"
    assert request.params == {}


def test_health_request_unknown_method_passes_validation() -> None:
    """Unknown methods are accepted at the envelope level.

    The dispatch table maps them to ``unknown_method`` later. The
    boundary model only enforces structural rules so that the wire
    format remains stable across schema changes.
    """

    request = HealthRequest.model_validate(
        {
            "protocol_version": 1,
            "request_id": "r-2",
            "method": "future/method",
        }
    )
    assert request.method == "future/method"


def test_health_request_rejects_missing_protocol_version() -> None:
    with pytest.raises(ValidationError):
        HealthRequest.model_validate({"request_id": "r-1", "method": "health/check"})


def test_health_request_rejects_wrong_protocol_version() -> None:
    with pytest.raises(ValidationError):
        HealthRequest.model_validate(
            {
                "protocol_version": 2,
                "request_id": "r-1",
                "method": "health/check",
            }
        )


def test_health_request_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        HealthRequest.model_validate(
            {
                "protocol_version": 1,
                "request_id": "r-1",
                "method": "health/check",
                "extra": True,
            }
        )


def test_health_request_rejects_non_dict_params() -> None:
    with pytest.raises(ValidationError):
        HealthRequest.model_validate(
            {
                "protocol_version": 1,
                "request_id": "r-1",
                "method": "health/check",
                "params": "not-a-dict",
            }
        )


def test_health_request_rejects_empty_request_id() -> None:
    with pytest.raises(ValidationError):
        HealthRequest.model_validate(
            {"protocol_version": 1, "request_id": "", "method": "health/check"}
        )


def test_health_success_round_trip() -> None:
    payload = {
        "protocol_version": 1,
        "request_id": "r-ok",
        "ok": True,
        "result": {"status": "ok", "version": "0.1.0", "timestamp": "t"},
    }
    envelope = HealthSuccess.model_validate(payload)
    dumped = json.loads(envelope.model_dump_json())
    assert dumped["protocol_version"] == 1
    assert dumped["ok"] is True
    assert dumped["result"]["status"] == "ok"


def test_health_failure_carries_stable_code() -> None:
    payload = {
        "protocol_version": 1,
        "request_id": "r-err",
        "ok": False,
        "error": {"code": "timeout", "message": "no reply in 3s"},
    }
    envelope = HealthFailure.model_validate(payload)
    dumped = json.loads(envelope.model_dump_json())
    assert dumped["error"]["code"] in {
        "backend_unavailable",
        "timeout",
        "invalid_protocol",
        "unknown_method",
    }


def test_health_failure_rejects_unknown_code() -> None:
    with pytest.raises(ValidationError):
        HealthFailure.model_validate(
            {
                "protocol_version": 1,
                "request_id": "r",
                "ok": False,
                "error": {"code": "made_up", "message": "x"},
            }
        )


def test_health_error_body_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        HealthErrorBody.model_validate(
            {"code": "timeout", "message": "x", "stack": "trace"}
        )


def test_health_result_shape() -> None:
    result = HealthResult(status="ok", version="0.1.0", timestamp="t")
    dumped = json.loads(result.model_dump_json())
    assert dumped == {"status": "ok", "version": "0.1.0", "timestamp": "t"}


def test_health_result_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        HealthResult(status="ok", version="0.1.0", timestamp="t", extra=1)


def test_known_methods_include_health_check() -> None:
    assert "health/check" in KNOWN_METHODS
