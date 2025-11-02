"""Betting repository implementations."""
from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Dict, Iterable, List, Sequence, Tuple

from ..events import BetConfirmationEvent
from ..models import Payoff
from ..portfolio import BetPosition, Portfolio
from .data_repository import DataRepository


CANONICAL_BET_TYPES: Dict[str, set[str]] = {
    "win": {"win", "単勝"},
    "place": {"place", "複勝"},
    "bracket_quinella": {"bracket_quinella", "枠連"},
    "quinella": {"quinella", "馬連"},
    "exacta": {"exacta", "馬単"},
    "quinella_place": {"quinella_place", "ワイド", "wide"},
    "trifecta_box": {"trifecta_box", "三連複"},
    "trifecta_exact": {"trifecta_exact", "三連単"},
}
"""Mappings from canonical bet types to their known aliases."""

ORDER_SENSITIVE = {"exacta", "trifecta_exact"}
"""Bet types where runner ordering matters when computing payoffs."""


def canonical_bet_type(bet_type: str) -> str:
    """Normalize different representations of a bet type."""

    normalized = bet_type.lower()
    for canonical, aliases in CANONICAL_BET_TYPES.items():
        if normalized in {alias.lower() for alias in aliases}:
            return canonical
    return normalized


@dataclass(slots=True)
class PendingBet:
    """Pending bet awaiting broker confirmation."""

    bet_id: str
    """Generated identifier for the pending bet."""
    race_id: str
    """Race identifier for the bet."""
    bet_type: str
    """Normalized bet type requested by the strategy."""
    combination: Tuple[str, ...]
    """Runner identifiers included in the bet."""
    stake: float
    """Stake reserved for the pending bet."""
    placed_at: datetime
    """Timestamp when the bet was requested."""


class BettingRepository(ABC):
    """Base class for bet execution backends."""

    def __init__(self, portfolio: Portfolio) -> None:
        """Initialise the repository with a backing portfolio."""

        self.portfolio = portfolio
        self._counter = itertools.count(1)

    def next_bet_id(self) -> str:
        """Return a new unique bet identifier."""

        return f"bet-{next(self._counter)}"

    def get_balance(self) -> float:
        """Return the available bankroll."""

        return self.portfolio.bankroll()

    def get_positions(self) -> List[BetPosition]:
        """Return all recorded positions."""

        return list(self.portfolio.positions.values())

    @abstractmethod
    def place_bet(
        self,
        race_id: str,
        horse_ids: Sequence[str],
        stake: float,
        bet_type: str,
        *,
        placed_at: datetime | None = None,
    ) -> BetConfirmationEvent | None:
        """Validate a bet request and return a confirmation event to enqueue."""

    @abstractmethod
    def confirm_bet(self, event: BetConfirmationEvent) -> BetPosition:
        """Finalize an accepted bet and add it to the portfolio."""

    @abstractmethod
    def settle_race(self, race_id: str) -> List[BetPosition]:
        """Settle all bets associated with a race."""


class SimulationBettingRepository(BettingRepository):
    """Betting repository that settles bets using simulation data."""

    def __init__(self, portfolio: Portfolio, data_repository: DataRepository) -> None:
        """Create a simulation repository backed by ``portfolio`` and data."""

        super().__init__(portfolio)
        self._data_repository = data_repository
        self._pending: Dict[str, List[BetPosition]] = {}
        self._pending_confirmations: Dict[str, PendingBet] = {}

    def _available_cash(self) -> float:
        """Return available cash excluding amounts reserved for pending bets."""

        reserved = sum(pending.stake for pending in self._pending_confirmations.values())
        return self.portfolio.cash - reserved

    def place_bet(
        self,
        race_id: str,
        horse_ids: Sequence[str],
        stake: float,
        bet_type: str,
        *,
        placed_at: datetime | None = None,
    ) -> BetConfirmationEvent:
        """Validate and reserve cash for a simulated bet request."""

        placement_time = placed_at or datetime.now(UTC)
        combination = tuple(horse_ids)
        if stake <= 0:
            return BetConfirmationEvent(
                bet_id=self.next_bet_id(),
                race_id=race_id,
                bet_type=bet_type,
                combination=combination,
                stake=stake,
                placed_at=placement_time,
                accepted=False,
                message=f"Stake must be positive, got {stake}",
            )
        if stake > self._available_cash():
            available = self._available_cash()
            return BetConfirmationEvent(
                bet_id=self.next_bet_id(),
                race_id=race_id,
                bet_type=bet_type,
                combination=combination,
                stake=stake,
                placed_at=placement_time,
                accepted=False,
                message=f"Insufficient cash to place bet (available {available:.2f})",
            )

        bet_id = self.next_bet_id()
        pending = PendingBet(
            bet_id=bet_id,
            race_id=race_id,
            bet_type=bet_type,
            combination=combination,
            stake=stake,
            placed_at=placement_time,
        )
        self._pending_confirmations[bet_id] = pending
        return BetConfirmationEvent(
            bet_id=bet_id,
            race_id=race_id,
            bet_type=bet_type,
            combination=combination,
            stake=stake,
            placed_at=placement_time,
            accepted=True,
        )

    def confirm_bet(self, event: BetConfirmationEvent) -> BetPosition:
        """Persist an accepted simulated bet and track it for settlement."""

        pending = self._pending_confirmations.pop(event.bet_id, None)
        if pending is None:
            msg = f"Unknown pending bet id: {event.bet_id}"
            raise KeyError(msg)
        position = self.portfolio.place_bet(
            bet_id=pending.bet_id,
            race_id=pending.race_id,
            bet_type=pending.bet_type,
            combination=pending.combination,
            stake=pending.stake,
            placed_at=pending.placed_at,
        )
        self._pending.setdefault(position.race_id, []).append(position)
        return position

    def settle_race(self, race_id: str) -> List[BetPosition]:
        """Settle all simulated bets for the given race identifier."""

        payoffs = list(self._data_repository.get_payoffs(race_id))
        settled: List[BetPosition] = []
        for position in self._pending.pop(race_id, []):
            payout = _calculate_payout(position, payoffs)
            settled.append(self.portfolio.settle_bet(position.bet_id, payout))
        return settled


class LiveBettingRepository(BettingRepository):
    """Placeholder repository representing an external broker."""

    def __init__(self, portfolio: Portfolio) -> None:
        """Initialise a repository that mimics live broker behaviour."""

        super().__init__(portfolio)
        self._pending_confirmations: Dict[str, PendingBet] = {}

    def _available_cash(self) -> float:
        """Return cash not yet reserved for submitted live bets."""

        reserved = sum(pending.stake for pending in self._pending_confirmations.values())
        return self.portfolio.cash - reserved

    def place_bet(
        self,
        race_id: str,
        horse_ids: Sequence[str],
        stake: float,
        bet_type: str,
        *,
        placed_at: datetime | None = None,
    ) -> BetConfirmationEvent:
        """Validate a live bet request and issue a confirmation."""

        placement_time = placed_at or datetime.now(UTC)
        combination = tuple(horse_ids)
        if stake <= 0:
            return BetConfirmationEvent(
                bet_id=self.next_bet_id(),
                race_id=race_id,
                bet_type=bet_type,
                combination=combination,
                stake=stake,
                placed_at=placement_time,
                accepted=False,
                message=f"Stake must be positive, got {stake}",
            )
        if stake > self._available_cash():
            available = self._available_cash()
            return BetConfirmationEvent(
                bet_id=self.next_bet_id(),
                race_id=race_id,
                bet_type=bet_type,
                combination=combination,
                stake=stake,
                placed_at=placement_time,
                accepted=False,
                message=f"Insufficient cash to place bet (available {available:.2f})",
            )

        bet_id = self.next_bet_id()
        pending = PendingBet(
            bet_id=bet_id,
            race_id=race_id,
            bet_type=bet_type,
            combination=combination,
            stake=stake,
            placed_at=placement_time,
        )
        self._pending_confirmations[bet_id] = pending
        return BetConfirmationEvent(
            bet_id=bet_id,
            race_id=race_id,
            bet_type=bet_type,
            combination=combination,
            stake=stake,
            placed_at=placement_time,
            accepted=True,
        )

    def settle_race(self, race_id: str) -> List[BetPosition]:
        """Return an empty list because live settlements happen asynchronously."""

        # Settlements are asynchronous in live mode; return empty list.
        return []

    def confirm_bet(self, event: BetConfirmationEvent) -> BetPosition:
        """Mark a confirmed bet as submitted to the external broker."""

        pending = self._pending_confirmations.pop(event.bet_id, None)
        if pending is None:
            msg = f"Unknown pending bet id: {event.bet_id}"
            raise KeyError(msg)
        position = self.portfolio.place_bet(
            bet_id=pending.bet_id,
            race_id=pending.race_id,
            bet_type=pending.bet_type,
            combination=pending.combination,
            stake=pending.stake,
            placed_at=pending.placed_at,
        )
        position.status = "submitted"
        return position


def _calculate_payout(position: BetPosition, payoffs: Iterable[Payoff]) -> float:
    """Return the payout for ``position`` using the supplied ``payoffs``."""

    canonical = canonical_bet_type(position.bet_type)
    for payoff in payoffs:
        payoff_type = canonical_bet_type(payoff.bet_type)
        if canonical != payoff_type:
            continue
        if _combinations_match(position.combination, payoff.combination, canonical):
            return position.stake * payoff.odds
    return 0.0


def _combinations_match(
    bet_combo: Sequence[str],
    result_combo: Sequence[str],
    canonical_type: str,
) -> bool:
    """Return whether the bet combination matches the payoff combination."""

    if canonical_type in ORDER_SENSITIVE:
        return tuple(bet_combo) == tuple(result_combo)
    if canonical_type == "win":
        return bet_combo and result_combo and bet_combo[0] == result_combo[0]
    if canonical_type == "place":
        return all(horse in result_combo for horse in bet_combo)
    if canonical_type in {"quinella", "quinella_place", "bracket_quinella", "trifecta_box"}:
        return set(bet_combo) == set(result_combo)
    return set(bet_combo) == set(result_combo)
