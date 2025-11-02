"""Clock abstractions for coordinating engine time."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime


class Clock(ABC):
    """Minimal clock interface used by the engine."""

    @abstractmethod
    def now(self) -> datetime:
        """Return the current time according to the clock."""

    def reset(self, start: datetime | None = None) -> None:
        """Reset the clock to a specific start time (optional)."""

    def advance_to(self, moment: datetime) -> None:
        """Advance the clock to the given moment if later than now."""


class RealClock(Clock):
    """Clock implementation that reflects wall-clock time."""

    def now(self) -> datetime:
        """Return the current wall-clock UTC time."""

        return datetime.now(UTC)

    def reset(self, start: datetime | None = None) -> None:  # pragma: no cover - trivial
        """Ignore resets because a real clock cannot be rewound."""

        # Real time clocks cannot be reset; ignore the hint.
        return None

    def advance_to(self, moment: datetime) -> None:  # pragma: no cover - trivial
        """Ignore advancement requests as wall-clock time is continuous."""

        # Nothing to do; the real clock is always moving forward.
        return None


class SimulatedClock(Clock):
    """Deterministic clock driven by historical data during simulations."""

    def __init__(self, start: datetime | None = None) -> None:
        """Create a simulated clock optionally initialised to ``start``."""

        self._now: datetime | None = None
        if start is not None:
            self.reset(start)

    def now(self) -> datetime:
        """Return the current simulated time in UTC."""

        if self._now is None:
            return datetime.now(UTC)
        return self._now

    def reset(self, start: datetime | None = None) -> None:
        """Reset the simulated clock to ``start`` or clear it."""

        self._now = _ensure_utc(start) if start is not None else None

    def advance_to(self, moment: datetime) -> None:
        """Advance the simulated clock to the provided ``moment``."""

        target = _ensure_utc(moment)
        if self._now is None or target > self._now:
            self._now = target


def _ensure_utc(moment: datetime) -> datetime:
    """Return a timezone-aware UTC datetime."""

    if moment.tzinfo is None:
        return moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC)

