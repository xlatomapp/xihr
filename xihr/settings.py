"""Configuration models for xihr applications."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AdaptorSettings(BaseModel):
    """Settings for configuring data adaptors."""

    path: Optional[Path] = None
    """Path to a directory of CSV files."""
    workbook: Optional[Path] = None
    """Path to an Excel workbook."""
    connection_url: Optional[str] = None
    """Database connection URL."""


class BettingLimits(BaseModel):
    """Constraints applied to betting operations."""

    max_stake: float = Field(default=1000.0, ge=0)
    """Maximum stake allowed per bet."""
    max_exposure: float = Field(default=10000.0, ge=0)
    """Maximum total exposure allowed across open bets."""


class AppSettings(BaseSettings):
    """Primary configuration object."""

    model_config = SettingsConfigDict(env_prefix="XIHR_", env_nested_delimiter="__")
    """Pydantic settings configuration for environment variable loading."""

    initial_bankroll: float = 10000.0
    """Default bankroll used when none is provided explicitly."""
    data_source: Literal["csv", "excel", "db"] = "csv"
    """Adaptor type to load racing data from."""
    adaptor_settings: AdaptorSettings = Field(default_factory=AdaptorSettings)
    """Nested adaptor configuration."""
    betting_limits: BettingLimits = Field(default_factory=BettingLimits)
    """Default betting constraints."""

    def ensure_bankroll(self, bankroll: float | None = None) -> float:
        """Validate ``bankroll`` or fall back to :attr:`initial_bankroll`."""

        value = bankroll if bankroll is not None else self.initial_bankroll
        if value <= 0:
            msg = "Bankroll must be positive"
            raise ValueError(msg)
        return value


def load_settings(**overrides) -> AppSettings:
    """Load settings merging environment variables and overrides."""

    return AppSettings(**overrides)
