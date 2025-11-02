"""Core engine orchestrating data, strategies, and betting."""
from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from datetime import UTC, datetime, time, timedelta
from inspect import signature
from itertools import count
from typing import Callable, Iterable, List, Literal, Sequence

from ._cron import croniter

from .clock import Clock, RealClock, SimulatedClock
from .events import (
    BetConfirmationEvent,
    BetRequestEvent,
    DataEvent,
    ResultEvent,
    TimeEvent,
)
from ..data.models import Race
from ..data.repositories import DataRepository, SimulationDataRepository
from ..execution.broker import BettingRepository

EventType = BetConfirmationEvent | BetRequestEvent | DataEvent | ResultEvent | TimeEvent
"""Union of all event variants processed by the engine."""


@dataclass(slots=True)
class ScheduleEntry:
    """Representation of a scheduled callback."""

    callback: Callable[..., None]
    """Callable executed when the schedule fires."""
    name: str
    """Human-readable name for the schedule."""
    mode: Literal["absolute", "relative", "cron"]
    """Scheduling mode that determines how the callback is triggered."""
    time_of_day: time | None = None
    """Absolute time of day for the schedule when ``mode`` is ``"absolute"``."""
    offset: timedelta | None = None
    """Offset relative to race start for ``"relative"`` schedules."""
    cron_expression: str | None = None
    """Cron expression used when ``mode`` is ``"cron"``."""
    next_due: datetime | None = None
    """Timestamp of the next activation for this schedule."""
    _relative_last_index: int = field(default=-1, init=False)
    """Index of the last race processed for a relative schedule."""
    _relative_target_index: int = field(default=-1, init=False)
    """Index of the upcoming race for a relative schedule."""
    _cron_iter: croniter | None = field(default=None, init=False)
    """Cached cron iterator for computing future activations."""

    def reset_for_run(self) -> None:
        """Reset cached scheduling information prior to starting a run."""

        self.next_due = None
        self._relative_last_index = -1
        self._relative_target_index = -1
        self._cron_iter = None

    def prepare(
        self,
        current: datetime,
        races: Sequence[Race],
        tick: timedelta,
        timeline_end: datetime,
    ) -> None:
        """Prepare the schedule for a run by computing its first due time."""

        current = _ensure_utc(current)
        if self.mode == "absolute":
            self.next_due = self._next_absolute(current, allow_equal=True)
        elif self.mode == "relative":
            self._relative_last_index = -1
            self._compute_relative_next(current, races)
        elif self.mode == "cron":
            base = current - tick
            self._cron_iter = croniter(self.cron_expression, base)
            self.next_due = _ensure_utc(self._cron_iter.get_next(datetime))
        if self.next_due is not None and self.next_due > timeline_end:
            self.next_due = None

    def advance(
        self,
        current: datetime,
        races: Sequence[Race],
        tick: timedelta,
        timeline_end: datetime,
    ) -> None:
        """Advance the schedule to the next activation after it fires."""

        current = _ensure_utc(current)
        if self.mode == "absolute":
            self.next_due = self._next_absolute(current, allow_equal=False)
        elif self.mode == "relative":
            self._relative_last_index = self._relative_target_index
            self._compute_relative_next(current, races)
        elif self.mode == "cron":
            if self._cron_iter is None:
                self._cron_iter = croniter(self.cron_expression, current)
            self.next_due = _ensure_utc(self._cron_iter.get_next(datetime))
        if self.next_due is not None and self.next_due > timeline_end:
            self.next_due = None

    def _next_absolute(self, current: datetime, *, allow_equal: bool) -> datetime:
        """Compute the next absolute trigger time for the schedule."""

        assert self.time_of_day is not None
        candidate = datetime.combine(current.date(), self.time_of_day, tzinfo=current.tzinfo)
        candidate = _ensure_utc(candidate)
        if candidate < current or (candidate == current and not allow_equal):
            candidate += timedelta(days=1)
        return candidate

    def _compute_relative_next(self, current: datetime, races: Sequence[Race]) -> None:
        """Determine the next trigger time relative to a future race."""

        assert self.offset is not None
        start_index = max(self._relative_last_index + 1, 0)
        for idx in range(start_index, len(races)):
            race_time = _ensure_utc(races[idx].date)
            trigger_time = race_time + self.offset
            if trigger_time >= current:
                self._relative_target_index = idx
                self.next_due = trigger_time
                return
        self.next_due = None
        self._relative_target_index = len(races)


class Engine:
    """Event-driven engine for running strategies."""

    def __init__(
        self,
        data_repository: DataRepository,
        betting_repository: BettingRepository,
        *,
        clock: Clock | None = None,
        tick_seconds: float = 1.0,
    ) -> None:
        """Initialise a new engine instance with repositories and clock settings."""

        if tick_seconds <= 0:
            msg = "tick_seconds must be a positive value"
            raise ValueError(msg)
        self.data_repository = data_repository
        self.betting_repository = betting_repository
        if clock is None and isinstance(data_repository, SimulationDataRepository):
            clock = SimulatedClock()
        self.clock: Clock = clock or RealClock()
        self._tick_interval = timedelta(seconds=float(tick_seconds))
        self._schedules: List[ScheduleEntry] = []
        self._event_queue: list[tuple[datetime, int, EventType]] = []
        self._counter = count()
        self._front_counter = count(-1, -1)
        self._next_tick_time: datetime | None = None
        self._races: list[Race] = []
        self._timeline_end: datetime | None = None
        self._running = False

    def schedule(
        self,
        when: str | time | datetime | None,
        callback: Callable[..., None],
        *,
        name: str | None = None,
        relative_to_race_start: timedelta | float | int | None = None,
        cron: str | None = None,
    ) -> None:
        if callback is None:
            msg = "callback must be provided"
            raise ValueError(msg)
        option_count = sum(
            1 for opt in (when, relative_to_race_start, cron) if opt is not None
        )
        if option_count != 1:
            msg = "Exactly one of when, relative_to_race_start, or cron must be provided"
            raise ValueError(msg)
        schedule_name = name or callback.__name__
        if when is not None:
            time_of_day = _parse_time_input(when)
            entry = ScheduleEntry(
                callback=callback,
                name=schedule_name,
                mode="absolute",
                time_of_day=time_of_day,
            )
        elif relative_to_race_start is not None:
            offset = _normalize_offset(relative_to_race_start)
            entry = ScheduleEntry(
                callback=callback,
                name=schedule_name,
                mode="relative",
                offset=offset,
            )
        else:
            assert cron is not None
            entry = ScheduleEntry(
                callback=callback,
                name=schedule_name,
                mode="cron",
                cron_expression=cron,
            )
        self._schedules.append(entry)
        if self._running:
            entry.reset_for_run()
            self._timeline_end = self._compute_timeline_end()
            entry.prepare(
                self.clock.now(),
                self._races,
                self._tick_interval,
                self._timeline_end,
            )
            self._schedule_next_tick()

    def run(self, strategy: "BaseStrategy") -> None:
        """Execute the engine loop for the provided strategy."""

        self._event_queue.clear()
        self._counter = count()
        self._front_counter = count(-1, -1)
        self._next_tick_time = None
        strategy.bind(self)
        races = list(_sorted_races(self.data_repository.iter_races()))
        self._races = races
        if isinstance(self.clock, SimulatedClock):
            start_time = _ensure_utc(races[0].date) if races else datetime.now(UTC)
        else:
            start_time = self.clock.now()
        self.clock.reset(start_time)
        self._timeline_end = _ensure_utc(start_time)
        self._running = True
        try:
            strategy.on_start()
            self._timeline_end = self._compute_timeline_end()
            now = self.clock.now()
            for entry in self._schedules:
                entry.reset_for_run()
                entry.prepare(now, self._races, self._tick_interval, self._timeline_end)
            for race in self._races:
                publish_at = self.data_repository.get_publish_time(race.race_id, "race")
                available_at = _ensure_utc(publish_at or race.date)
                if available_at < now:
                    available_at = now
                self._enqueue(
                    DataEvent(kind="race", race=race, available_at=available_at)
                )
                payoff_publish = self.data_repository.get_publish_time(
                    race.race_id, "payoff"
                )
                if payoff_publish is not None:
                    publish_time = _ensure_utc(payoff_publish)
                    if publish_time < available_at:
                        publish_time = available_at
                    if publish_time < now:
                        publish_time = now
                    self._enqueue(
                        DataEvent(kind="payoff", race=race, available_at=publish_time)
                    )
            initial_tick = self.clock.now()
            self._next_tick_time = initial_tick
            self._enqueue(TimeEvent(name="tick", scheduled_for=initial_tick))
            self._process_events(strategy)
        finally:
            self._running = False
            self._next_tick_time = None
            self._timeline_end = None

    def submit_bet(self, event: BetRequestEvent) -> None:
        """Queue a bet request event for processing."""

        if event.placed_at is None:
            event.placed_at = self.clock.now()
        event.placed_at = _ensure_utc(event.placed_at)
        self._enqueue(event)

    def _enqueue(self, event: EventType) -> None:
        """Add an event to the priority queue for later processing."""

        when = _event_time(event)
        order = next(self._front_counter) if isinstance(event, TimeEvent) else next(self._counter)
        heapq.heappush(self._event_queue, (when, order, event))

    def _enqueue_front(self, event: EventType) -> None:
        """Insert an event at the front of the queue while preserving ordering."""

        when = _event_time(event)
        order = next(self._front_counter)
        heapq.heappush(self._event_queue, (when, order, event))

    def _process_events(self, strategy: "BaseStrategy") -> None:
        """Process events until the queue is exhausted."""

        while self._event_queue:
            scheduled_for, _, event = heapq.heappop(self._event_queue)
            scheduled_for = _ensure_utc(scheduled_for)
            if isinstance(event, TimeEvent):
                self._next_tick_time = None
                event.scheduled_for = scheduled_for
                self.clock.advance_to(scheduled_for)
                strategy.on_time(event)
                self._run_due_schedules(strategy, scheduled_for)
                self._schedule_next_tick()
            elif isinstance(event, DataEvent):
                event.available_at = scheduled_for
                self.clock.advance_to(event.available_at)
                if event.kind == "payoff":
                    payoffs = tuple(
                        self.data_repository.get_payoffs(event.race.race_id)
                    )
                    event.payoffs = payoffs
                strategy.on_data(event)
                if event.kind == "payoff":
                    settled = self.betting_repository.settle_race(event.race.race_id)
                    if settled:
                        self._enqueue(
                            ResultEvent(
                                race_id=event.race.race_id,
                                settled_at=self.clock.now(),
                            )
                        )
            elif isinstance(event, BetRequestEvent):
                event.placed_at = scheduled_for
                self.clock.advance_to(event.placed_at)
                confirmation = self.betting_repository.place_bet(
                    race_id=event.race_id,
                    horse_ids=event.combination,
                    stake=event.stake,
                    bet_type=event.bet_type,
                    placed_at=event.placed_at,
                )
                if confirmation is not None:
                    self._enqueue_front(confirmation)
            elif isinstance(event, BetConfirmationEvent):
                event.placed_at = scheduled_for
                self.clock.advance_to(event.placed_at)
                if event.accepted:
                    position = self.betting_repository.confirm_bet(event)
                    event.position = position
                    settled = self.betting_repository.settle_race(event.race_id)
                    if settled:
                        self._enqueue(
                            ResultEvent(
                                race_id=event.race_id,
                                settled_at=self.clock.now(),
                            )
                        )
                strategy.on_bet(event)
            elif isinstance(event, ResultEvent):
                event.settled_at = scheduled_for
                self.clock.advance_to(event.settled_at)
                strategy.on_result(event)

    def _run_due_schedules(self, strategy: "BaseStrategy", current_time: datetime) -> None:
        """Invoke any schedules that are due at the provided time."""

        if self._timeline_end is None:
            return
        now = _ensure_utc(current_time)
        for entry in self._schedules:
            while entry.next_due is not None and now >= entry.next_due:
                self._invoke_schedule(entry, strategy)
                entry.advance(now, self._races, self._tick_interval, self._timeline_end)

    def _invoke_schedule(self, entry: ScheduleEntry, strategy: "BaseStrategy") -> None:
        """Execute a scheduled callback, optionally providing the strategy."""

        params = signature(entry.callback).parameters
        if not params:
            entry.callback()
        else:
            entry.callback(strategy)

    def _schedule_next_tick(self) -> None:
        """Determine and enqueue the next tick event if needed."""

        if not self._running:
            return
        has_non_time = any(
            not isinstance(event, TimeEvent) for _, _, event in self._event_queue
        )
        has_schedule = any(entry.next_due is not None for entry in self._schedules)
        if not has_non_time and not has_schedule:
            return
        now = _ensure_utc(self.clock.now())
        if isinstance(self.clock, SimulatedClock):
            candidate_times = [
                when
                for when, _, event in self._event_queue
                if when > now and not isinstance(event, TimeEvent)
            ]
            candidate_times.extend(
                entry.next_due for entry in self._schedules if entry.next_due and entry.next_due > now
            )
            if not candidate_times:
                return
            next_tick_time = min(candidate_times)
        else:
            next_tick_time = now + self._tick_interval
        if self._timeline_end is not None and next_tick_time > self._timeline_end:
            return
        if self._next_tick_time is not None and next_tick_time >= self._next_tick_time:
            return
        self._next_tick_time = next_tick_time
        self._enqueue(TimeEvent(name="tick", scheduled_for=next_tick_time))

    def _compute_timeline_end(self) -> datetime:
        """Calculate the timeline upper bound for the current run."""

        if not self._races:
            return _ensure_utc(self.clock.now())
        last_race_time = max(_ensure_utc(race.date) for race in self._races)
        max_offset = max(
            (
                entry.offset
                for entry in self._schedules
                if entry.mode == "relative" and entry.offset and entry.offset > timedelta(0)
            ),
            default=timedelta(0),
        )
        timeline_end = last_race_time + max_offset
        payoff_times = [
            _ensure_utc(publish)
            for publish in (
                self.data_repository.get_publish_time(race.race_id, "payoff")
                for race in self._races
            )
            if publish is not None
        ]
        if payoff_times:
            timeline_end = max(timeline_end, max(payoff_times))
        # Allow absolute/cron schedules to run through the final race day without
        # keeping the simulation alive indefinitely.
        timeline_end = max(timeline_end, last_race_time + timedelta(days=1))
        return timeline_end


def _sorted_races(races: Iterable[Race]) -> List[Race]:
    """Return the races sorted by their scheduled datetime."""

    return sorted(races, key=lambda race: race.date)


def _ensure_utc(moment: datetime) -> datetime:
    """Normalize datetimes to explicit UTC timezone objects."""

    if moment.tzinfo is None:
        return moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC)


def _event_time(event: EventType) -> datetime:
    """Extract the scheduling timestamp for a given event instance."""

    if isinstance(event, TimeEvent):
        event.scheduled_for = _ensure_utc(event.scheduled_for)
        return event.scheduled_for
    if isinstance(event, DataEvent):
        event.available_at = _ensure_utc(event.available_at)
        return event.available_at
    if isinstance(event, BetRequestEvent):
        if event.placed_at is None:
            msg = "BetRequestEvent must define placed_at before enqueueing"
            raise ValueError(msg)
        event.placed_at = _ensure_utc(event.placed_at)
        return event.placed_at
    if isinstance(event, BetConfirmationEvent):
        event.placed_at = _ensure_utc(event.placed_at)
        return event.placed_at
    if isinstance(event, ResultEvent):
        event.settled_at = _ensure_utc(event.settled_at)
        return event.settled_at
    msg = f"Unsupported event type: {type(event)!r}"
    raise TypeError(msg)


def _parse_time_input(value: str | time | datetime) -> time:
    """Normalise user provided schedule inputs into a ``time`` instance."""

    if isinstance(value, time):
        return value
    if isinstance(value, datetime):
        return value.timetz() if value.tzinfo is not None else value.time()
    if isinstance(value, str):
        try:
            return time.fromisoformat(value)
        except ValueError as exc:  # pragma: no cover - defensive
            msg = f"Invalid time string: {value}"
            raise ValueError(msg) from exc
    msg = f"Unsupported time input: {value!r}"
    raise TypeError(msg)


def _normalize_offset(value: timedelta | float | int) -> timedelta:
    """Convert various offset representations into a ``timedelta``."""

    if isinstance(value, timedelta):
        return value
    if isinstance(value, (int, float)):
        return timedelta(seconds=float(value))
    msg = f"Unsupported offset type: {type(value)!r}"
    raise TypeError(msg)
