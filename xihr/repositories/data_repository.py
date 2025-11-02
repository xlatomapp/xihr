"""Data repositories provide access to racing data for strategies."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from typing import Dict, Iterable, Iterator, List, Literal

from ..adaptors import DataAdaptor
from ..models import Payoff, Race, to_domain_payoff, to_domain_race


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
    """Repository backed by a :class:`DataAdaptor` for simulations."""

    def __init__(
        self,
        adaptor: DataAdaptor,
        *,
        payoff_publication_delay: timedelta | float | int = timedelta(minutes=10),
    ) -> None:
        """Load race and payoff data from the adaptor for simulations."""

        self._race_models = list(adaptor.load_races())
        self._payoff_models = list(adaptor.load_payoffs())

        self._races: Dict[str, Race] = {model.race_id: to_domain_race(model) for model in self._race_models}
        self._payoffs_by_race: Dict[str, List[Payoff]] = {}
        for payoff_model in self._payoff_models:
            self._payoffs_by_race.setdefault(payoff_model.race_id, []).append(
                to_domain_payoff(payoff_model)
            )
        if isinstance(payoff_publication_delay, (int, float)):
            payoff_publication_delay = timedelta(minutes=float(payoff_publication_delay))
        self._payoff_delay: timedelta = payoff_publication_delay

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
