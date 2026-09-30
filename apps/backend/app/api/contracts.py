"""Pydantic boundary models for the IPC envelope.

These models are the single source of truth for the wire format that
crosses the Python Agent Runtime boundary. The stdio engine parses
incoming requests through ``HealthRequest`` and validates outgoing
responses through ``HealthSuccess`` / ``HealthErrorBody``. Errors
raised by ``ValidationError`` are translated into the stable
``invalid_protocol`` error code so that the wire format stays
predictable for the Rust host and the React frontend.

Iteration 02 introduces these models. The wire format is unchanged;
Pydantic replaces the previous manual field checks.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

PROTOCOL_VERSION: Literal[1] = 1

ErrorCode = Literal[
    "backend_unavailable",
    "timeout",
    "invalid_protocol",
    "unknown_method",
]

KNOWN_METHODS: tuple[str, ...] = ("health/check",)


class EnvelopeBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def _require_protocol_version(cls, data: Any) -> Any:
        if isinstance(data, dict) and "protocol_version" not in data:
            raise ValueError("protocol_version is required")
        return data

    @model_validator(mode="after")
    def _check_protocol_version(self) -> "EnvelopeBase":
        if self.protocol_version != PROTOCOL_VERSION:
            raise ValueError(f"unsupported protocol_version: {self.protocol_version!r}")
        return self

    protocol_version: Literal[1] = PROTOCOL_VERSION


class HealthRequest(EnvelopeBase):
    method: str = Field(min_length=1)
    params: dict[str, object] = Field(default_factory=dict)


class HealthResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    version: str
    timestamp: str


class HealthSuccess(EnvelopeBase):
    ok: Literal[True] = True
    result: dict


class HealthErrorBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: ErrorCode
    message: str = Field(min_length=1)


class HealthFailure(EnvelopeBase):
    ok: Literal[False] = False
    error: HealthErrorBody
