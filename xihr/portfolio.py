"""Portfolio and position tracking primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Dict, List, Sequence


@dataclass(slots=True)
class BetPosition:
    """Represents a bet placed by a strategy."""

    bet_id: str
    """Unique identifier of the bet."""
    race_id: str
    """Race the bet is associated with."""
    bet_type: str
    """Type of wager placed."""
    combination: Sequence[str]
    """Runners included in the wager."""
    stake: float
    """Stake committed to the bet."""
    placed_at: datetime
    """Timestamp the bet was placed."""
    status: str = "open"
    """Current status of the bet (open or settled)."""
    payout: float = 0.0
    """Payout received once the bet is settled."""


@dataclass
class Portfolio:
    """Simple bankroll tracker."""

    initial_bankroll: float
    """Starting bankroll value."""
    cash: float
    """Available cash not tied up in open bets."""
    positions: Dict[str, BetPosition] = field(default_factory=dict)
    """Mapping from bet identifier to position details."""

    @classmethod
    def create(cls, bankroll: float) -> "Portfolio":
        """Create a new portfolio seeded with ``bankroll`` cash."""

        return cls(initial_bankroll=bankroll, cash=bankroll)

    def place_bet(
        self,
        *,
        bet_id: str,
        race_id: str,
        bet_type: str,
        combination: Sequence[str],
        stake: float,
        placed_at: datetime | None = None,
    ) -> BetPosition:
        """Reserve stake for a bet and store the resulting position."""

        if stake <= 0:
            msg = f"Stake must be positive, got {stake}"
            raise ValueError(msg)
        if stake > self.cash:
            msg = "Insufficient cash to place bet"
            raise ValueError(msg)
        position = BetPosition(
            bet_id=bet_id,
            race_id=race_id,
            bet_type=bet_type,
            combination=tuple(combination),
            stake=stake,
            placed_at=placed_at or datetime.now(UTC),
        )
        self.cash -= stake
        self.positions[bet_id] = position
        return position

    def settle_bet(self, bet_id: str, payout: float) -> BetPosition:
        """Settle the specified bet and release any winnings."""

        position = self.positions.get(bet_id)
        if position is None:
            msg = f"Unknown bet id: {bet_id}"
            raise KeyError(msg)
        if position.status != "open":
            msg = f"Bet {bet_id} already settled"
            raise ValueError(msg)
        position.status = "settled"
        position.payout = payout
        self.cash += payout
        return position

    def bankroll(self) -> float:
        """Return the current cash balance."""

        return self.cash

    def open_positions(self) -> List[BetPosition]:
        """Return positions that have not yet settled."""

        return [pos for pos in self.positions.values() if pos.status == "open"]

    def settled_positions(self) -> List[BetPosition]:
        """Return positions that have settled."""

        return [pos for pos in self.positions.values() if pos.status == "settled"]

    def total_profit(self) -> float:
        """Calculate the combined realized and unrealized profit."""

        realized = sum(pos.payout - pos.stake for pos in self.settled_positions())
        unrealized = -sum(pos.stake for pos in self.open_positions())
        return realized + unrealized
