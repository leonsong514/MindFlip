"""Health service.

Returns a deterministic OK response. Intentionally does not touch the
database, network, or any model provider, and has no third-party
runtime dependencies. The result proves that the Python runtime is
reachable and that the message envelope is wired correctly.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class HealthResult:
    status: str
    version: str
    timestamp: str


def health_status(version: str) -> HealthResult:
    return HealthResult(
        status="ok",
        version=version,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def health_payload(version: str) -> dict[str, str]:
    return asdict(health_status(version))