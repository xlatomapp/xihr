"""Reporting helpers for backtest runs."""

from __future__ import annotations

from typing import Iterable

from .metrics import KPIReport, generate_report
from ..strategy.risk import BetPosition


def summarize(positions: Iterable[BetPosition]) -> KPIReport:
    """Return a :class:`KPIReport` for ``positions``."""

    return generate_report(list(positions))


__all__ = ["summarize"]
