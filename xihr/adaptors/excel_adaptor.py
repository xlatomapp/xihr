"""Excel-backed data adaptor implementation."""

from __future__ import annotations

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


class ExcelDataAdaptor(DataAdaptor):
    """Load data from an Excel workbook with named sheets."""

    def __init__(
        self,
        workbook: str | Path,
        *,
        races_sheet: str = "races",
        horses_sheet: str = "horses",
        payoffs_sheet: str = "payoffs",
    ) -> None:
        """Create an adaptor bound to a workbook and sheet names."""

        self.workbook = Path(workbook)
        self.races_sheet = races_sheet
        self.horses_sheet = horses_sheet
        self.payoffs_sheet = payoffs_sheet

    def _load_sheet(self, sheet_name: str) -> pd.DataFrame:
        """Load a sheet from the workbook into a DataFrame."""

        if not self.workbook.exists():
            msg = f"Excel workbook not found: {self.workbook}"
            raise FileNotFoundError(msg)
        return pd.read_excel(self.workbook, sheet_name=sheet_name)

    def load_races(self) -> Sequence[RaceModel]:
        """Load races and horse entries from the workbook."""

        horses_df = self._load_sheet(self.horses_sheet)
        if "odds" in horses_df.columns:
            horses_df["odds"] = horses_df["odds"].apply(_ensure_dict)
        races_df = self._load_sheet(self.races_sheet)
        races_df["date"] = pd.to_datetime(races_df["date"])

        horses = validate_and_build_horses(horses_df)
        return validate_and_build_races(races_df, horses)

    def load_payoffs(self) -> Iterable[PayoffModel]:
        """Load payoff rows from the configured sheet."""

        payoffs_df = self._load_sheet(self.payoffs_sheet)
        payoffs_df["combination"] = payoffs_df["combination"].apply(_convert_combination)
        return validate_and_build_payoffs(payoffs_df)


def _convert_combination(raw: object) -> tuple[str, ...]:
    """Normalise combination cells to a tuple of runner identifiers."""

    if isinstance(raw, (list, tuple)):
        return tuple(str(item) for item in raw)
    if isinstance(raw, str):
        return tuple(part.strip() for part in raw.split("-"))
    raise ValueError(f"Unsupported combination format: {raw!r}")


def _ensure_dict(raw: object) -> dict:
    """Ensure odds data is a dictionary."""

    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        import json

        return json.loads(raw)
    raise ValueError(f"Unsupported odds format: {raw!r}")
