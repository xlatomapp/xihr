"""Command line interface for running simulations and reports."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Type

import pandas as pd
import typer
import yaml

from .analytics import generate_report
from .engine import Engine
from .portfolio import Portfolio
from .repositories import (
    LiveBettingRepository,
    LiveDataRepository,
    SimulationBettingRepository,
    SimulationDataRepository,
)
from .settings import AppSettings, load_settings
from .strategy import BaseStrategy
from strategies import NaiveFavoriteStrategy, ValueBettingStrategy

app = typer.Typer(help="Japanese horse racing betting simulator")

STRATEGIES: Dict[str, Type[BaseStrategy]] = {
    "naive_favorite": NaiveFavoriteStrategy,
    "value_betting": ValueBettingStrategy,
}
"""Registry of strategies exposed to the CLI."""


@app.command()
def run(
    *,
    strategy: str = typer.Option("naive_favorite", help="Strategy name"),
    data_source: str = typer.Option("csv", help="Data source: csv|excel|db"),
    data: Path = typer.Option(..., exists=False, help="Path to data source"),
    bankroll: float | None = typer.Option(None, help="Override bankroll"),
    config: Path | None = typer.Option(None, help="Optional YAML config file"),
    live: bool = typer.Option(False, help="Run in live mode"),
    output: Path | None = typer.Option(None, help="Path to save bet history"),
) -> None:
    """Run a strategy with the provided configuration."""

    settings = _load_config(config)
    bankroll_value = settings.ensure_bankroll(bankroll)

    portfolio = Portfolio.create(bankroll_value)

    simulation_repository = _create_simulation_repository(
        data_source or settings.data_source,
        settings,
        data,
    )

    if live:
        data_repository = _prime_live_repository(simulation_repository)
        betting_repository = LiveBettingRepository(portfolio)
    else:
        data_repository = simulation_repository
        betting_repository = SimulationBettingRepository(portfolio, data_repository)

    engine = Engine(data_repository, betting_repository)
    strategy_instance = _load_strategy(strategy)
    engine.run(strategy_instance)

    report = generate_report(betting_repository.get_positions())
    typer.echo(
        f"Bets: {report.settled_bets}/{report.total_bets} | Win rate: {report.win_rate:.1%} | ROI: {report.roi:.2f}"
    )
    if output:
        _write_positions(output, betting_repository.get_positions())
        typer.echo(f"Saved bet history to {output}")


@app.command()
def report(*, bets: Path = typer.Option(..., exists=True, help="CSV bet history")) -> None:
    """Generate analytics for a saved bet history."""

    df = pd.read_csv(bets)
    positions = [
        portfolio_row_to_position(row)
        for _, row in df.iterrows()
    ]
    kpi = generate_report(positions)
    typer.echo(f"Win rate: {kpi.win_rate:.1%}")
    typer.echo(f"ROI: {kpi.roi:.2f}")
    typer.echo(f"Total profit: {kpi.total_profit:.2f}")


def _load_strategy(name: str) -> BaseStrategy:
    """Instantiate a strategy by name from the :data:`STRATEGIES` registry."""

    key = name.lower()
    if key not in STRATEGIES:
        msg = f"Unknown strategy '{name}'. Available: {', '.join(STRATEGIES)}"
        raise typer.BadParameter(msg)
    return STRATEGIES[key]()


def _create_simulation_repository(
    source: str,
    settings: AppSettings,
    data_path: Path,
) -> SimulationDataRepository:
    """Create a simulation repository based on CLI options and settings."""

    choice = source.lower()
    if choice == "csv":
        path = data_path if data_path.is_dir() else data_path.parent
        if not path.exists():
            raise typer.BadParameter("CSV data directory does not exist")
        return SimulationDataRepository.from_csv(path)
    if choice == "excel":
        if not data_path.exists():
            raise typer.BadParameter("Excel workbook does not exist")
        return SimulationDataRepository.from_excel(data_path)
    if choice == "db":
        connection = settings.data_source_settings.connection_url
        if not connection:
            raise typer.BadParameter(
                "Database connection URL must be provided in settings"
            )
        return SimulationDataRepository.from_database(connection)
    raise typer.BadParameter(f"Unsupported data source: {source}")


def _prime_live_repository(
    simulation_repository: SimulationDataRepository,
) -> LiveDataRepository:
    """Populate a live repository with data sourced from simulation inputs."""

    live_repo = LiveDataRepository()
    for race in simulation_repository.iter_races():
        live_repo.register_race(race)
        publish_time = simulation_repository.get_publish_time(race.race_id, "race")
        if publish_time is not None:
            live_repo.register_publish_time(race.race_id, "race", publish_time)
        payoffs = simulation_repository.get_payoffs(race.race_id)
        for payoff in payoffs:
            live_repo.register_payoff(payoff)
        publish_time = simulation_repository.get_publish_time(race.race_id, "payoff")
        if publish_time is not None:
            live_repo.register_publish_time(race.race_id, "payoff", publish_time)
    return live_repo


def _load_config(config_path: Path | None) -> AppSettings:
    """Load application settings optionally merging a YAML file."""

    overrides: Dict[str, Any] = {}
    if config_path:
        with config_path.open("r", encoding="utf8") as fh:
            overrides = yaml.safe_load(fh) or {}
    return load_settings(**overrides)


def _write_positions(path: Path, positions) -> None:
    """Persist portfolio positions to ``path`` as CSV."""

    records = [
        {
            "bet_id": pos.bet_id,
            "race_id": pos.race_id,
            "bet_type": pos.bet_type,
            "combination": "-".join(pos.combination),
            "stake": pos.stake,
            "payout": pos.payout,
            "status": pos.status,
        }
        for pos in positions
    ]
    pd.DataFrame(records).to_csv(path, index=False)


def portfolio_row_to_position(row: pd.Series):
    """Convert a CSV row into a :class:`~xihr.portfolio.BetPosition`."""

    from xihr.portfolio import BetPosition
    from datetime import UTC, datetime

    combination_raw = str(row.get("combination", ""))
    combo = tuple(part for part in combination_raw.split("-") if part)
    return BetPosition(
        bet_id=str(row["bet_id"]),
        race_id=str(row.get("race_id", "")),
        bet_type=str(row.get("bet_type", "")),
        combination=combo,
        stake=float(row["stake"]),
        placed_at=datetime.now(UTC),
        status=str(row.get("status", "settled")),
        payout=float(row.get("payout", 0.0)),
    )
