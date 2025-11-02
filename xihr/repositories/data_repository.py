"""Data repositories provide access to racing data for strategies."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Literal, Sequence

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from ..models import (
    Payoff,
    PayoffModel,
    Race,
    RaceModel,
    to_domain_payoff,
    to_domain_race,
    validate_and_build_horses,
    validate_and_build_payoffs,
    validate_and_build_races,
)


class DataRepository(ABC):
    """Abstract base repository used by strategies and the engine."""

    @abstractmethod
    def get_race(self, race_id: str) -> Race | None:
        """Return the race with the given identifier."""

    @abstractmethod
    def iter_races(self) -> Iterator[Race]:
        """Iterate through available races."""

    @abstractmethod
    def get_payoffs(self, race_id: str) -> Iterable[Payoff]:
        """Return payoffs for a specific race."""

    @abstractmethod
    def get_historical(self, horse_id: str) -> Dict[str, float]:
        """Return historical statistics for the given horse."""

    @abstractmethod
    def get_publish_time(
        self, race_id: str, data_type: Literal["race", "payoff"]
    ) -> datetime | None:
        """Return when a given data type becomes available for a race."""


class SimulationDataRepository(DataRepository):
    """Repository that serves static datasets for simulations."""

    def __init__(
        self,
        races: Sequence[RaceModel],
        payoffs: Iterable[PayoffModel],
        *,
        payoff_publication_delay: timedelta | float | int = timedelta(minutes=10),
    ) -> None:
        """Initialise the repository with validated race and payoff models."""

        self._race_models = list(races)
        self._payoff_models = list(payoffs)

        self._races: Dict[str, Race] = {
            model.race_id: to_domain_race(model) for model in self._race_models
        }
        self._payoffs_by_race: Dict[str, List[Payoff]] = {}
        for payoff_model in self._payoff_models:
            self._payoffs_by_race.setdefault(payoff_model.race_id, []).append(
                to_domain_payoff(payoff_model)
            )
        if isinstance(payoff_publication_delay, (int, float)):
            payoff_publication_delay = timedelta(minutes=float(payoff_publication_delay))
        self._payoff_delay: timedelta = payoff_publication_delay

    @classmethod
    def from_csv(
        cls,
        base_path: str | Path,
        *,
        races_file: str = "races.csv",
        horses_file: str = "horses.csv",
        payoffs_file: str = "payoffs.csv",
        payoff_publication_delay: timedelta | float | int = timedelta(minutes=10),
    ) -> "SimulationDataRepository":
        """Create a repository from CSV files stored beneath ``base_path``."""

        base = Path(base_path)
        horses_df = _load_csv(base / horses_file, converters={"odds": json.loads})
        races_df = _load_csv(base / races_file, parse_dates=["date"])
        payoffs_df = _load_csv(
            base / payoffs_file, converters={"combination": _parse_combination}
        )

        horses = validate_and_build_horses(horses_df)
        races = validate_and_build_races(races_df, horses)
        payoffs = validate_and_build_payoffs(payoffs_df)
        return cls(
            races,
            payoffs,
            payoff_publication_delay=payoff_publication_delay,
        )

    @classmethod
    def from_excel(
        cls,
        workbook: str | Path,
        *,
        races_sheet: str = "races",
        horses_sheet: str = "horses",
        payoffs_sheet: str = "payoffs",
        payoff_publication_delay: timedelta | float | int = timedelta(minutes=10),
    ) -> "SimulationDataRepository":
        """Create a repository from an Excel workbook."""

        workbook_path = Path(workbook)
        horses_df = _load_excel(workbook_path, horses_sheet)
        if "odds" in horses_df.columns:
            horses_df["odds"] = horses_df["odds"].apply(_ensure_dict)
        races_df = _load_excel(workbook_path, races_sheet)
        races_df["date"] = pd.to_datetime(races_df["date"])
        payoffs_df = _load_excel(workbook_path, payoffs_sheet)
        payoffs_df["combination"] = payoffs_df["combination"].apply(_convert_combination)

        horses = validate_and_build_horses(horses_df)
        races = validate_and_build_races(races_df, horses)
        payoffs = validate_and_build_payoffs(payoffs_df)
        return cls(
            races,
            payoffs,
            payoff_publication_delay=payoff_publication_delay,
        )

    @classmethod
    def from_database(
        cls,
        engine: str | Engine,
        *,
        races_table: str = "races",
        horses_table: str = "horses",
        payoffs_table: str = "payoffs",
        payoff_publication_delay: timedelta | float | int = timedelta(minutes=10),
    ) -> "SimulationDataRepository":
        """Create a repository backed by relational tables."""

        sql_engine: Engine = create_engine(engine) if isinstance(engine, str) else engine
        horses_df = _load_table(sql_engine, horses_table)
        if "odds" in horses_df.columns:
            horses_df["odds"] = horses_df["odds"].apply(_ensure_dict)
        races_df = _load_table(sql_engine, races_table)
        races_df["date"] = pd.to_datetime(races_df["date"])
        payoffs_df = _load_table(sql_engine, payoffs_table)
        payoffs_df["combination"] = payoffs_df["combination"].apply(_convert_combination)

        horses = validate_and_build_horses(horses_df)
        races = validate_and_build_races(races_df, horses)
        payoffs = validate_and_build_payoffs(payoffs_df)
        return cls(
            races,
            payoffs,
            payoff_publication_delay=payoff_publication_delay,
        )

    def get_race(self, race_id: str) -> Race | None:
        """Return a cached race by identifier, if available."""

        return self._races.get(race_id)

    def iter_races(self) -> Iterator[Race]:
        """Iterate through races in chronological order."""

        return iter(sorted(self._races.values(), key=lambda race: race.date))

    def get_payoffs(self, race_id: str) -> Iterable[Payoff]:
        """Return payoffs for the given race identifier."""

        return tuple(self._payoffs_by_race.get(race_id, ()))

    def get_historical(self, horse_id: str) -> Dict[str, float]:
        """Compute simple win statistics for a horse across races."""

        wins = 0
        starts = 0
        for race in self._races.values():
            if race.get_horse(horse_id):
                starts += 1
        for race_payoffs in self._payoffs_by_race.values():
            for payoff in race_payoffs:
                if horse_id in payoff.combination and payoff.bet_type in {"win", "単勝"}:
                    wins += 1
        if starts == 0:
            return {"starts": 0, "wins": 0, "win_rate": 0.0}
        return {"starts": starts, "wins": wins, "win_rate": wins / starts}

    def get_publish_time(
        self, race_id: str, data_type: Literal["race", "payoff"]
    ) -> datetime | None:
        """Return when a race or payoff becomes available in simulation."""

        race = self.get_race(race_id)
        if race is None:
            return None
        race_time = _ensure_utc(race.date)
        if data_type == "race":
            return race_time
        if data_type == "payoff":
            return race_time + self._payoff_delay
        msg = f"Unsupported data type: {data_type}"
        raise ValueError(msg)


class LiveDataRepository(DataRepository):
    """Repository placeholder for live data sources."""

    def __init__(self) -> None:
        """Create an empty repository representing live feeds."""

        self._races: Dict[str, Race] = {}
        self._payoffs: Dict[str, List[Payoff]] = {}
        self._publish_times: Dict[tuple[str, str], datetime] = {}

    def register_race(self, race: Race) -> None:
        """Insert or update a race entry."""

        self._races[race.race_id] = race

    def register_payoff(self, payoff: Payoff) -> None:
        """Register a payoff entry for later retrieval."""

        self._payoffs.setdefault(payoff.race_id, []).append(payoff)

    def get_race(self, race_id: str) -> Race | None:
        """Return a registered live race if present."""

        return self._races.get(race_id)

    def iter_races(self) -> Iterator[Race]:
        """Iterate over races currently registered."""

        return iter(self._races.values())

    def get_payoffs(self, race_id: str) -> Iterable[Payoff]:
        """Return payoffs that have been registered for the race."""

        return tuple(self._payoffs.get(race_id, ()))

    def get_historical(self, horse_id: str) -> Dict[str, float]:
        """Return placeholder stats when historical data is unavailable."""

        # In live mode we may not have historical data. Provide empty stats.
        return {"starts": 0, "wins": 0, "win_rate": 0.0}

    def register_publish_time(
        self, race_id: str, data_type: Literal["race", "payoff"], available_at: datetime
    ) -> None:
        """Register when specific data will become available."""

        self._publish_times[(race_id, data_type)] = _ensure_utc(available_at)

    def get_publish_time(
        self, race_id: str, data_type: Literal["race", "payoff"]
    ) -> datetime | None:
        """Return the registered publish time for a race and data type."""

        return self._publish_times.get((race_id, data_type))


def _ensure_utc(moment: datetime) -> datetime:
    """Return a timezone-aware UTC datetime."""

    if moment.tzinfo is None:
        return moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC)


def _load_csv(path: Path, **kwargs) -> pd.DataFrame:
    """Load a CSV file from ``path`` into a DataFrame."""

    if not path.exists():
        msg = f"CSV file not found: {path}"
        raise FileNotFoundError(msg)
    return pd.read_csv(path, **kwargs)


def _load_excel(path: Path, sheet_name: str) -> pd.DataFrame:
    """Load an Excel sheet into a DataFrame."""

    if not path.exists():
        msg = f"Excel workbook not found: {path}"
        raise FileNotFoundError(msg)
    return pd.read_excel(path, sheet_name=sheet_name)


def _load_table(engine: Engine, table: str) -> pd.DataFrame:
    """Load an entire SQL table into a DataFrame."""

    return pd.read_sql_table(table, engine)


def _parse_combination(raw: str) -> tuple[str, ...]:
    """Convert a serialized combination cell into a tuple of horse ids."""

    raw = raw.strip()
    if not raw:
        return tuple()
    if raw.startswith("["):
        try:
            values = pd.io.json.loads(raw)
        except ValueError as exc:  # pragma: no cover - defensive fallback
            msg = f"Invalid combination json: {raw}"
            raise ValueError(msg) from exc
        return tuple(str(item) for item in values)
    return tuple(part.strip() for part in raw.split("-"))


def _convert_combination(raw: object) -> tuple[str, ...]:
    """Normalise a combination representation to a tuple of runner ids."""

    if isinstance(raw, (list, tuple)):
        return tuple(str(item) for item in raw)
    if isinstance(raw, str):
        return tuple(part.strip() for part in raw.split("-"))
    msg = f"Unsupported combination format: {raw!r}"
    raise ValueError(msg)


def _ensure_dict(raw: object) -> dict:
    """Ensure stored odds data is expressed as a dictionary."""

    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        return json.loads(raw)
    msg = f"Unsupported odds format: {raw!r}"
    raise ValueError(msg)
