"""Command line interface for running xihr strategies."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Type

import pandas as pd
import typer
import yaml

from .adaptors import CSVDataAdaptor, DBDataAdaptor, ExcelDataAdaptor
from .analytics import generate_report
from .engine import Engine
from .models import to_domain_payoff, to_domain_race
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
    adaptor: str = typer.Option("csv", help="Data adaptor: csv|excel|db"),
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

    adaptor_instance = _create_adaptor(adaptor or settings.data_source, settings, data)

    if live:
        data_repository = LiveDataRepository()
        for race_model in adaptor_instance.load_races():
            data_repository.register_race(to_domain_race(race_model))
        for payoff_model in adaptor_instance.load_payoffs():
            data_repository.register_payoff(to_domain_payoff(payoff_model))
        betting_repository = LiveBettingRepository(portfolio)
    else:
        data_repository = SimulationDataRepository(adaptor_instance)
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


def _create_adaptor(adaptor: str, settings: AppSettings, data_path: Path):
    """Create a data adaptor instance based on CLI options and settings."""

    adaptor = adaptor.lower()
    if adaptor == "csv":
        path = data_path if data_path.is_dir() else data_path.parent
        if not path.exists():
            raise typer.BadParameter("CSV data directory does not exist")
        return CSVDataAdaptor(path)
    if adaptor == "excel":
        if not data_path.exists():
            raise typer.BadParameter("Excel workbook does not exist")
        return ExcelDataAdaptor(data_path)
    if adaptor == "db":
        connection = settings.adaptor_settings.connection_url
        if not connection:
            raise typer.BadParameter("Database connection URL must be provided in settings")
        return DBDataAdaptor(connection)
    raise typer.BadParameter(f"Unsupported adaptor: {adaptor}")


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
