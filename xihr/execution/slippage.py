"""Backtest-only slippage models."""

from __future__ import annotations

from typing import Protocol


class SlippageModel(Protocol):
    """Protocol for modelling execution slippage during backtests."""

    def apply(self, price: float, volume: float) -> float:  # pragma: no cover - interface stub
        """Return the adjusted price after accounting for slippage."""


class NoSlippage:
    """Trivial slippage model returning the original price."""

    def apply(self, price: float, volume: float) -> float:
        return price


__all__ = ["SlippageModel", "NoSlippage"]
