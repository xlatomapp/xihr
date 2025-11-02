"""Backtesting utilities and evaluation helpers."""

from .metrics import KPIReport, generate_report
from .simulator import SimulationResult

__all__ = ["KPIReport", "generate_report", "SimulationResult"]
