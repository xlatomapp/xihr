"""Internal helper that provides a ``croniter`` compatible interface."""

from __future__ import annotations

import importlib
from datetime import datetime, timedelta
from typing import Any, Callable, Optional


def _load_croniter() -> Optional[Callable[[str, datetime], Any]]:
    """Attempt to load :func:`croniter` from the external dependency."""

    spec = importlib.util.find_spec("croniter")
    if spec is None:  # pragma: no cover - exercised when dependency is missing
        return None
    module = importlib.import_module("croniter")
    return getattr(module, "croniter", None)


class _FallbackCroniter:
    """Small subset of the :mod:`croniter` API used by the engine."""

    def __init__(self, expression: str, start_time: datetime) -> None:
        self._current = start_time.replace(second=0, microsecond=0)
        parts = expression.split()
        if len(parts) != 5:  # pragma: no cover - defensive
            raise ValueError(f"Unsupported cron expression: {expression}")
        self._minute = None if parts[0] == "*" else int(parts[0])
        self._hour = None if parts[1] == "*" else int(parts[1])
        self._day = None if parts[2] == "*" else int(parts[2])
        self._month = None if parts[3] == "*" else int(parts[3])
        self._weekday = None if parts[4] == "*" else int(parts[4])

    def get_next(self, _: type[datetime]) -> datetime:
        """Return the next activation matching the expression."""

        candidate = self._current
        while True:
            candidate = (candidate + timedelta(minutes=1)).replace(second=0, microsecond=0)
            if self._minute is not None and candidate.minute != self._minute:
                continue
            if self._hour is not None and candidate.hour != self._hour:
                continue
            if self._day is not None and candidate.day != self._day:
                continue
            if self._month is not None and candidate.month != self._month:
                continue
            if self._weekday is not None and candidate.weekday() != self._weekday:
                continue
            self._current = candidate
            return candidate


def croniter(expression: str, start_time: datetime) -> Any:
    """Return a cron iterator using the real dependency when available."""

    factory = _load_croniter()
    if factory is not None:
        return factory(expression, start_time)
    return _FallbackCroniter(expression, start_time)


__all__ = ["croniter"]
