"""CSV-backed data adaptor implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd

from ..models import (
    PayoffModel,
    RaceModel,
    validate_and_build_horses,
    validate_and_build_payoffs,
    validate_and_build_races,
)
from .base import DataAdaptor


class CSVDataAdaptor(DataAdaptor):
    """Load racing data from CSV files stored under a directory."""

    def __init__(
        self,
        base_path: str | Path,
        *,
        races_file: str = "races.csv",
        horses_file: str = "horses.csv",
        payoffs_file: str = "payoffs.csv",
    ) -> None:
        """Create an adaptor bound to ``base_path`` with optional file overrides."""

        self.base_path = Path(base_path)
        self.races_file = races_file
        self.horses_file = horses_file
        self.payoffs_file = payoffs_file

    def _load_csv(self, filename: str, **kwargs) -> pd.DataFrame:
        """Load a CSV file from disk and return it as a :class:`DataFrame`."""

        path = self.base_path / filename
        if not path.exists():
            msg = f"CSV file not found: {path}"
            raise FileNotFoundError(msg)
        return pd.read_csv(path, **kwargs)

    def load_races(self) -> Sequence[RaceModel]:
        """Load races and their participants from disk."""

        horses_df = self._load_csv(self.horses_file, converters={"odds": json.loads})
        races_df = self._load_csv(self.races_file, parse_dates=["date"])

        horses = validate_and_build_horses(horses_df)
        return validate_and_build_races(races_df, horses)

    def load_payoffs(self) -> Iterable[PayoffModel]:
        """Load payoff records for the configured races."""

        payoffs_df = self._load_csv(self.payoffs_file, converters={"combination": _parse_combination})
        return validate_and_build_payoffs(payoffs_df)


def _parse_combination(raw: str) -> tuple[str, ...]:
    """Convert a serialized combination cell into a tuple of horse ids."""

    raw = raw.strip()
    if not raw:
        return tuple()
    if raw.startswith("["):
        try:
            values = pd.io.json.loads(raw)
        except ValueError as exc:  # pragma: no cover - defensive fallback
            raise ValueError(f"Invalid combination json: {raw}") from exc
        return tuple(str(item) for item in values)
    return tuple(part.strip() for part in raw.split("-"))
