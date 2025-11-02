"""Adaptor abstraction for loading racing data."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Sequence

from ..models import PayoffModel, RaceModel


class DataAdaptor(ABC):
    """Base interface for loading racing and payoff data."""

    @abstractmethod
    def load_races(self) -> Sequence[RaceModel]:
        """Return a sequence of :class:`RaceModel` instances."""

    @abstractmethod
    def load_payoffs(self) -> Iterable[PayoffModel]:
        """Return payoff models for the loaded races."""
