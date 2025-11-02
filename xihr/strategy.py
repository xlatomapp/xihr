"""Base strategy abstractions."""
from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from typing import Callable, Sequence

from .engine import Engine
from .events import (
    BetConfirmationEvent,
    BetRequestEvent,
    DataEvent,
    ResultEvent,
    TimeEvent,
)
from .portfolio import BetPosition, Portfolio
from .repositories import BettingRepository, DataRepository


class BaseStrategy:
    """Base class implementing the strategy API described in the project spec."""

    def __init__(self, *, name: str | None = None) -> None:
        """Initialise the strategy with an optional human friendly ``name``."""

        self.name = name or self.__class__.__name__
        self.engine: Engine | None = None
        self.data_repository: DataRepository | None = None
        self.betting_repository: BettingRepository | None = None
        self.portfolio: Portfolio | None = None

    # -- lifecycle -----------------------------------------------------
    def bind(self, engine: Engine) -> None:
        """Bind the strategy to an engine before the run starts."""

        self.engine = engine
        self.data_repository = engine.data_repository
        self.betting_repository = engine.betting_repository
        self.portfolio = engine.betting_repository.portfolio

    # -- scheduling ----------------------------------------------------
    def schedule(
        self,
        when_or_callback: str | time | datetime | Callable[["BaseStrategy"], None],
        fn: Callable[["BaseStrategy"], None] | None = None,
        *,
        name: str | None = None,
        relative_to_race_start: timedelta | float | int | None = None,
        cron: str | None = None,
    ) -> None:
        """Schedule a callback using absolute, relative, or cron semantics."""

        if self.engine is None:
            msg = "Strategy must be bound to an engine before scheduling"
            raise RuntimeError(msg)
        if callable(when_or_callback) and fn is None:
            callback = when_or_callback
            when: str | time | datetime | None = None
        else:
            when = when_or_callback
            callback = fn
        if callback is None:
            msg = "A callback function must be provided for scheduling"
            raise ValueError(msg)
        schedule_name = name or f"{self.name}:{callback.__name__}"
        when_value: str | time | datetime | None
        if isinstance(when, (str, time, datetime)):
            when_value = when
        elif when is None:
            when_value = None
        else:  # pragma: no cover - defensive branch
            msg = "Unsupported schedule time specification"
            raise TypeError(msg)
        self.engine.schedule(
            when_value,
            callback,
            name=schedule_name,
            relative_to_race_start=relative_to_race_start,
            cron=cron,
        )

    # -- data access ---------------------------------------------------
    def get_data(self, race_id: str, bet_type: str | None = None) -> DataEvent | None:
        """Return race data for ``race_id`` if available."""

        if self.data_repository is None:
            return None
        race = self.data_repository.get_race(race_id)
        if race is None:
            return None
        if self.engine is None:
            available_at = datetime.now(UTC)
        else:
            available_at = self.engine.clock.now()
        return DataEvent(kind="race", race=race, available_at=available_at)

    def get_historical(self, horse_id: str) -> dict[str, float]:
        """Return historical stats for a horse if the repository supports it."""

        if self.data_repository is None:
            return {}
        return self.data_repository.get_historical(horse_id)

    # -- betting -------------------------------------------------------
    def place_bet(
        self,
        race_id: str,
        horse_ids: Sequence[str],
        stake: float,
        bet_type: str,
        *,
        placed_at: datetime | None = None,
    ) -> None:
        """Create a bet request event and enqueue it on the engine."""

        if self.engine is None:
            msg = "Strategy must be bound to an engine before placing bets"
            raise RuntimeError(msg)
        event = BetRequestEvent(
            race_id=race_id,
            bet_type=bet_type,
            combination=tuple(horse_ids),
            stake=stake,
            placed_at=placed_at or (self.engine.clock.now() if self.engine else None),
        )
        self.engine.submit_bet(event)

    def get_balance(self) -> float:
        """Return the current bankroll from the betting repository."""

        if self.betting_repository is None:
            return 0.0
        return self.betting_repository.get_balance()

    def get_positions(self) -> list[BetPosition]:
        """Return current positions managed by the betting repository."""

        if self.betting_repository is None:
            return []
        return self.betting_repository.get_positions()

    # -- hooks ---------------------------------------------------------
    def on_start(self) -> None:  # pragma: no cover - extension point
        """Called before the engine starts processing races."""

    def on_time(self, event: TimeEvent) -> None:  # pragma: no cover - extension point
        """Called when a scheduled time event is triggered."""

    def on_data(self, event: DataEvent) -> None:  # pragma: no cover - extension point
        """Called when the engine publishes new data (e.g. race cards or payoffs)."""

    def on_bet(self, event: BetConfirmationEvent) -> None:  # pragma: no cover - extension point
        """Called when a bet has been placed."""

    def on_result(self, event: ResultEvent) -> None:  # pragma: no cover - extension point
        """Called when a race result has been processed."""
