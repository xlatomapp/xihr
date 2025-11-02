"""Database adaptor using SQLAlchemy."""
from __future__ import annotations

from typing import Iterable, Sequence

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from ..models import (
    PayoffModel,
    RaceModel,
    validate_and_build_horses,
    validate_and_build_payoffs,
    validate_and_build_races,
)
from .base import DataAdaptor


class DBDataAdaptor(DataAdaptor):
    """Adaptor that pulls race data from relational tables."""

    def __init__(
        self,
        engine: str | Engine,
        *,
        races_table: str = "races",
        horses_table: str = "horses",
        payoffs_table: str = "payoffs",
    ) -> None:
        """Create an adaptor using the provided SQLAlchemy ``engine``."""

        self.engine: Engine = create_engine(engine) if isinstance(engine, str) else engine
        self.races_table = races_table
        self.horses_table = horses_table
        self.payoffs_table = payoffs_table

    def _load_table(self, table: str) -> pd.DataFrame:
        """Load an entire SQL table into a pandas :class:`DataFrame`."""

        return pd.read_sql_table(table, self.engine)

    def load_races(self) -> Sequence[RaceModel]:
        """Fetch races and participating horses from database tables."""

        horses_df = self._load_table(self.horses_table)
        if "odds" in horses_df.columns:
            horses_df["odds"] = horses_df["odds"].apply(_ensure_dict)
        races_df = self._load_table(self.races_table)
        races_df["date"] = pd.to_datetime(races_df["date"])

        horses = validate_and_build_horses(horses_df)
        return validate_and_build_races(races_df, horses)

    def load_payoffs(self) -> Iterable[PayoffModel]:
        """Fetch payoff rows and convert them into models."""

        payoffs_df = self._load_table(self.payoffs_table)
        payoffs_df["combination"] = payoffs_df["combination"].apply(_convert_combination)
        return validate_and_build_payoffs(payoffs_df)


def _convert_combination(raw: object) -> tuple[str, ...]:
    """Normalize a stored combination representation to a tuple of strings."""

    if isinstance(raw, str):
        return tuple(part.strip() for part in raw.split("-"))
    if isinstance(raw, (list, tuple)):
        return tuple(str(item) for item in raw)
    raise ValueError(f"Unsupported combination format: {raw!r}")


def _ensure_dict(raw: object) -> dict:
    """Ensure odds data is represented as a dictionary."""

    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        import json

        return json.loads(raw)
    raise ValueError(f"Unsupported odds format: {raw!r}")
