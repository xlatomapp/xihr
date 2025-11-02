"""Event definitions used by the engine and strategies."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Sequence

from ..data.models import Payoff, Race
from ..strategy.risk import BetPosition


@dataclass(slots=True)
class TimeEvent:
    """Tick event emitted by the engine clock."""

    name: str
    """Identifier for the tick source."""
    scheduled_for: datetime
    """Timestamp when the tick is scheduled to occur."""


@dataclass(slots=True)
class DataEvent:
    """Event representing new data being published by the repositories."""

    kind: Literal["race", "payoff"]
    """Type of data emitted (race card or payoff)."""
    race: Race
    """Race associated with the event."""
    available_at: datetime
    """Timestamp when the data becomes available."""
    payoffs: tuple[Payoff, ...] = ()
    """Optional payoff payload included with the event."""


@dataclass(slots=True)
class BetRequestEvent:
    """Event raised by a strategy requesting a bet to be placed."""

    race_id: str
    """Identifier of the race for the request."""
    bet_type: str
    """Type of bet that should be placed."""
    combination: Sequence[str]
    """Runner identifiers involved in the bet."""
    stake: float
    """Stake amount requested for the bet."""
    placed_at: datetime | None = None
    """Optional timestamp supplied by the strategy."""


@dataclass(slots=True)
class BetConfirmationEvent:
    """Event emitted by the broker once a bet request is processed."""

    bet_id: str
    """Unique identifier assigned by the broker."""
    race_id: str
    """Race associated with the confirmation."""
    bet_type: str
    """Type of bet that was processed."""
    combination: Sequence[str]
    """Runner identifiers contained in the confirmation."""
    stake: float
    """Stake amount accepted or rejected."""
    placed_at: datetime
    """Timestamp when the bet was processed."""
    accepted: bool
    """Flag indicating whether the bet was accepted."""
    message: str | None = None
    """Optional broker message describing the outcome."""
    position: BetPosition | None = None
    """Portfolio position generated for accepted bets."""


@dataclass(slots=True)
class ResultEvent:
    """Event emitted when a race has settled."""

    race_id: str
    """Identifier for the settled race."""
    settled_at: datetime
    """Timestamp when the race was settled."""


