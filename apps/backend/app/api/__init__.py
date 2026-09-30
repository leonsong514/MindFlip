"""Application API surface.

This package holds transport-facing services. In iteration 01 it
exposes the deterministic health probe and the stdio IPC engine that
adapts the envelope in `packages/contracts`. Persistence and domain
services are added in later iterations and must not be imported from
here.

Iteration 02 adds Pydantic boundary models in `contracts`; the IPC
engine validates incoming envelopes through them and the Pydantic
types are the source of truth for the wire shape.
"""

from .health import health_payload, health_status
from .ipc import (
    PROTOCOL_VERSION,
    ProtocolError,
    build_error_response,
    build_success_response,
    dispatch,
    handle_line,
    parse_request,
)
from .contracts import (
    KNOWN_METHODS,
    HealthErrorBody,
    HealthFailure,
    HealthRequest,
    HealthResult,
    HealthSuccess,
)

__all__ = [
    "health_status",
    "health_payload",
    "PROTOCOL_VERSION",
    "ProtocolError",
    "parse_request",
    "dispatch",
    "build_success_response",
    "build_error_response",
    "handle_line",
    "KNOWN_METHODS",
    "HealthErrorBody",
    "HealthFailure",
    "HealthRequest",
    "HealthResult",
    "HealthSuccess",
]
