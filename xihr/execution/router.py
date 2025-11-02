"""Order routing utilities and throttling controls."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable


@dataclass(slots=True)
class Throttle:
    """Simple throttling helper ensuring a minimum delay between actions."""

    interval: timedelta
    last_executed: datetime | None = None

    def allow(self, now: datetime) -> bool:
        """Return ``True`` if execution is allowed at ``now``."""

        if self.last_executed is None:
            self.last_executed = now
            return True
        if now - self.last_executed >= self.interval:
            self.last_executed = now
            return True
        return False


def any_throttle_allows(throttles: Iterable[Throttle], now: datetime) -> bool:
    """Return ``True`` if at least one throttle would allow execution."""

    return any(throttle.allow(now) for throttle in throttles)


__all__ = ["Throttle", "any_throttle_allows"]
