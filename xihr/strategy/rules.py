"""Composable building blocks for filtering and ranking signals."""

from __future__ import annotations

from typing import Iterable, Protocol, Sequence, TypeVar

from .risk import BetPosition

SignalT = TypeVar("SignalT")


class Rule(Protocol[SignalT]):
    """Protocol for rule components that transform signals."""

    def apply(self, signals: Sequence[SignalT]) -> Sequence[SignalT]:  # pragma: no cover - interface stub
        """Return a possibly filtered or re-ordered sequence of ``signals``."""


def limit_open_positions(positions: Iterable[BetPosition], max_open: int) -> bool:
    """Return ``True`` if fewer than ``max_open`` positions are currently open."""

    open_positions = sum(1 for position in positions if position.status == "open")
    return open_positions < max_open


__all__ = ["Rule", "limit_open_positions"]
