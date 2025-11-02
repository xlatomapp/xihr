"""Application settings and configuration models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional


@dataclass(slots=True)
class DataSourceSettings:
    """Settings for configuring data repositories."""

    path: Optional[Path] = None
    """Path to a directory of CSV files."""
    workbook: Optional[Path] = None
    """Path to an Excel workbook."""
    connection_url: Optional[str] = None
    """Database connection URL."""


@dataclass(slots=True)
class BettingLimits:
    """Constraints applied to betting operations."""

    max_stake: float = 1000.0
    """Maximum stake allowed per bet."""
    max_exposure: float = 10000.0
    """Maximum total exposure allowed across open bets."""


@dataclass(slots=True)
class AppSettings:
    """Primary configuration object."""

    initial_bankroll: float = 10000.0
    """Default bankroll used when none is provided explicitly."""
    data_source: Literal["csv", "excel", "db"] = "csv"
    """Repository type to load racing data from."""
    data_source_settings: DataSourceSettings = field(default_factory=DataSourceSettings)
    """Nested repository configuration."""
    betting_limits: BettingLimits = field(default_factory=BettingLimits)
    """Default betting constraints."""

    def ensure_bankroll(self, bankroll: float | None = None) -> float:
        """Validate ``bankroll`` or fall back to :attr:`initial_bankroll`."""

        value = bankroll if bankroll is not None else self.initial_bankroll
        if value <= 0:
            msg = "Bankroll must be positive"
            raise ValueError(msg)
        return value


def load_settings(**overrides) -> AppSettings:
    """Load settings merging optional overrides."""

    data_source_overrides = overrides.pop("data_source_settings", None)
    betting_overrides = overrides.pop("betting_limits", None)
    settings = AppSettings(**overrides)
    if data_source_overrides is not None:
        settings.data_source_settings = DataSourceSettings(**data_source_overrides)
    if betting_overrides is not None:
        settings.betting_limits = BettingLimits(**betting_overrides)
    return settings


__all__ = [
    "AppSettings",
    "BettingLimits",
    "DataSourceSettings",
    "load_settings",
]
