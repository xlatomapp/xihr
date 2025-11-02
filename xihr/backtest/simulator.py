"""Market simulation utilities for backtesting strategies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from ..core.events import ResultEvent
from ..strategy.risk import BetPosition, Portfolio


@dataclass(slots=True)
class SimulationResult:
    """Summary information returned after running a backtest."""

    positions: Sequence[BetPosition]
    events: Sequence[ResultEvent]


def run_simulation(portfolio: Portfolio, events: Iterable[ResultEvent]) -> SimulationResult:
    """Replay ``events`` against ``portfolio`` returning the resulting state."""

    positions = list(portfolio.settled_positions())
    result_events = list(events)
    return SimulationResult(positions=positions, events=result_events)


__all__ = ["SimulationResult", "run_simulation"]
