"""Health and readiness checks for long running services."""

from __future__ import annotations

from enum import Enum
from typing import Protocol


class HealthStatus(str, Enum):
    """Enumeration of coarse health states."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class HealthCheck(Protocol):
    """Protocol describing a callable health check."""

    def __call__(self) -> HealthStatus:  # pragma: no cover - interface stub
        """Return the current health status."""


def health_check(check: HealthCheck) -> bool:
    """Return ``True`` when ``check`` reports :class:`HealthStatus.HEALTHY`."""

    return check() is HealthStatus.HEALTHY


__all__ = ["HealthStatus", "HealthCheck", "health_check"]
