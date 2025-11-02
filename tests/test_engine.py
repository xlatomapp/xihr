"""Integration tests covering engine workflows."""

from pathlib import Path

from datetime import UTC, datetime, timedelta

from xihr.analytics import generate_report
from xihr.engine import Engine
from xihr.portfolio import Portfolio
from xihr.repositories import SimulationBettingRepository, SimulationDataRepository
from strategies import NaiveFavoriteStrategy
from xihr.strategy import BaseStrategy


def test_csv_repository_loads_sample_data():
    """Ensure the CSV-backed repository loads races and payoffs from fixtures."""

    repository = SimulationDataRepository.from_csv(Path("data/sample"))
    races = list(repository.iter_races())
    payoffs = [
        payoff
        for race in races
        for payoff in repository.get_payoffs(race.race_id)
    ]

    assert len(races) == 2
    assert all(race.horses for race in races)
    assert any(payoff.bet_type == "win" for payoff in payoffs)


def test_engine_runs_naive_strategy(tmp_path):
    """Execute a strategy end-to-end and confirm results are recorded."""

    data_repo = SimulationDataRepository.from_csv(Path("data/sample"))
    portfolio = Portfolio.create(1000)
    betting_repo = SimulationBettingRepository(portfolio, data_repo)
    engine = Engine(data_repo, betting_repo)

    strategy = NaiveFavoriteStrategy()
    engine.run(strategy)

    positions = betting_repo.get_positions()
    assert positions
    report = generate_report(positions)
    assert report.settled_bets == len(positions)
    assert report.total_bets == len(positions)


def test_simulated_clock_advances_with_history():
    """Validate that the simulated clock aligns with historical data."""

    data_repo = SimulationDataRepository.from_csv(Path("data/sample"))
    portfolio = Portfolio.create(1000)
    betting_repo = SimulationBettingRepository(portfolio, data_repo)
    engine = Engine(data_repo, betting_repo)

    strategy = NaiveFavoriteStrategy()
    engine.run(strategy)

    positions = betting_repo.get_positions()
    assert {pos.placed_at.tzinfo for pos in positions} == {UTC}
    race_dates = {}
    for race in data_repo.iter_races():
        race_dates[race.race_id] = (
            race.date.replace(tzinfo=UTC)
            if race.date.tzinfo is None
            else race.date.astimezone(UTC)
        )
    for position in positions:
        assert position.placed_at.date() == race_dates[position.race_id].date()

    last_race_date = max(race_dates.values())
    assert engine.clock.now() >= last_race_date


def test_event_driven_tick_and_schedule():
    """Verify that absolute, relative, and cron schedules fire correctly."""

    data_repo = SimulationDataRepository.from_csv(Path("data/sample"))
    portfolio = Portfolio.create(1000)
    betting_repo = SimulationBettingRepository(portfolio, data_repo)
    engine = Engine(data_repo, betting_repo)

    class ScheduledStrategy(NaiveFavoriteStrategy):
        """Strategy capturing engine callbacks for schedule assertions."""

        def __init__(self) -> None:
            """Initialise tracking containers for schedule invocations."""

            super().__init__()
            self.time_events: list[datetime] = []
            """Timestamps received from time events."""
            self.absolute_invocations: list[datetime] = []
            """Timestamps recorded for absolute schedules."""
            self.relative_invocations: list[datetime] = []
            """Timestamps recorded for relative schedules."""
            self.cron_invocations: list[datetime] = []
            """Timestamps recorded for cron schedules."""

        def on_start(self) -> None:
            """Register schedule callbacks using all supported modes."""

            super().on_start()
            self.schedule("00:00", self._absolute_callback)
            self.schedule(
                self._relative_callback,
                relative_to_race_start=timedelta(hours=1),
            )
            self.schedule(self._cron_callback, cron="0 0 * * *")

        def on_time(self, event):
            """Record clock ticks for later verification."""

            self.time_events.append(event.scheduled_for)
            return super().on_time(event)

        def _absolute_callback(self, _: BaseStrategy) -> None:
            """Record invocation time for absolute schedule callback."""

            assert self.engine is not None
            self.absolute_invocations.append(self.engine.clock.now())

        def _relative_callback(self, _: BaseStrategy) -> None:
            """Record invocation time for relative schedule callback."""

            assert self.engine is not None
            self.relative_invocations.append(self.engine.clock.now())

        def _cron_callback(self, _: BaseStrategy) -> None:
            """Record invocation time for cron schedule callback."""

            assert self.engine is not None
            self.cron_invocations.append(self.engine.clock.now())

    strategy = ScheduledStrategy()
    engine.run(strategy)

    assert strategy.absolute_invocations
    assert strategy.absolute_invocations[0] == datetime(2024, 4, 1, tzinfo=UTC)
    assert strategy.relative_invocations == [
        datetime(2024, 4, 1, 1, tzinfo=UTC),
        datetime(2024, 4, 2, 1, tzinfo=UTC),
    ]
    assert strategy.cron_invocations == [
        datetime(2024, 4, 1, tzinfo=UTC),
        datetime(2024, 4, 2, tzinfo=UTC),
        datetime(2024, 4, 3, tzinfo=UTC),
    ]
    # Ensure tick events advanced directly to the relevant schedule boundaries
    expected_ticks = {
        datetime(2024, 4, 1, tzinfo=UTC),
        datetime(2024, 4, 1, 1, tzinfo=UTC),
        datetime(2024, 4, 2, tzinfo=UTC),
        datetime(2024, 4, 2, 1, tzinfo=UTC),
        datetime(2024, 4, 3, tzinfo=UTC),
    }
    assert expected_ticks.issubset(set(strategy.time_events))
    assert engine.clock.now() == datetime(2024, 4, 3, tzinfo=UTC)


def test_engine_schedules_payoff_publication():
    data_repo = SimulationDataRepository.from_csv(
        Path("data/sample"), payoff_publication_delay=timedelta(minutes=45)
    )
    portfolio = Portfolio.create(1000)
    betting_repo = SimulationBettingRepository(portfolio, data_repo)
    engine = Engine(data_repo, betting_repo)

    class CaptureStrategy(NaiveFavoriteStrategy):
        def __init__(self) -> None:
            super().__init__()
            self.data_events: list[tuple[str, datetime]] = []

        def on_data(self, event):
            self.data_events.append((event.kind, event.available_at))
            return super().on_data(event)

    strategy = CaptureStrategy()
    engine.run(strategy)

    payoff_events = [ts for kind, ts in strategy.data_events if kind == "payoff"]
    assert payoff_events
    expected_first = data_repo.get_publish_time("RACE001", "payoff")
    assert expected_first is not None
    assert payoff_events[0] == expected_first
