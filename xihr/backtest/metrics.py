"""Analytics helpers for computing betting KPIs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from ..strategy.risk import BetPosition


@dataclass(slots=True)
class KPIReport:
    """Container for summary statistics."""

    total_bets: int
    """Number of bets placed."""
    settled_bets: int
    """Number of bets that have been settled."""
    win_rate: float
    """Win ratio for settled bets."""
    roi: float
    """Return on investment for settled bets."""
    avg_payout: float
    """Average payout for settled bets."""
    total_profit: float
    """Net profit across settled bets."""
    max_drawdown: float
    """Maximum drawdown experienced in the run."""
    max_consecutive_win: int
    """Longest winning streak."""
    max_consecutive_loss: int
    """Longest losing streak."""


def generate_report(positions: Iterable[BetPosition]) -> KPIReport:
    """Aggregate the provided positions into a :class:`KPIReport`."""

    position_list = list(positions)
    total_bets = len(position_list)
    if total_bets == 0:
        return KPIReport(0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0)

    settled = [pos for pos in position_list if pos.status == "settled"]
    settled_bets = len(settled)
    if settled_bets == 0:
        return KPIReport(total_bets, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0)

    profits = [pos.payout - pos.stake for pos in settled]
    total_profit = sum(profits)
    total_stake = sum(pos.stake for pos in settled)
    roi = total_profit / total_stake if total_stake else 0.0
    wins = [pos.payout > pos.stake for pos in settled]
    win_rate = sum(1 for won in wins if won) / settled_bets
    avg_payout = sum(pos.payout for pos in settled) / settled_bets
    max_drawdown = _calculate_drawdown(profits)
    max_win, max_loss = _streaks(wins)

    return KPIReport(
        total_bets=total_bets,
        settled_bets=settled_bets,
        win_rate=float(win_rate),
        roi=float(roi),
        avg_payout=float(avg_payout),
        total_profit=float(total_profit),
        max_drawdown=float(max_drawdown),
        max_consecutive_win=max_win,
        max_consecutive_loss=max_loss,
    )


def _calculate_drawdown(profits: List[float]) -> float:
    """Compute the maximum drawdown for a sequence of incremental profits."""

    cumulative = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for profit in profits:
        cumulative += profit
        peak = max(peak, cumulative)
        drawdown = peak - cumulative
        max_drawdown = max(max_drawdown, drawdown)
    return max_drawdown


def _streaks(results: List[bool]) -> tuple[int, int]:
    """Return maximum winning and losing streak lengths."""

    max_win = 0
    max_loss = 0
    current_win = 0
    current_loss = 0
    for won in results:
        if won:
            current_win += 1
            current_loss = 0
        else:
            current_loss += 1
            current_win = 0
        max_win = max(max_win, current_win)
        max_loss = max(max_loss, current_loss)
    return max_win, max_loss


__all__ = ["KPIReport", "generate_report"]
