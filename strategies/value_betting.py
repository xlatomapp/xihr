"""Value betting strategy that uses historical win rates."""
from __future__ import annotations

from xihr.strategy import BaseStrategy


class ValueBettingStrategy(BaseStrategy):
    """Strategy that bets when historical win rates imply positive value."""

    stake: float = 50.0
    """Stake size for qualified runners."""
    edge_threshold: float = 1.2
    """Minimum expected value multiplier required to place a bet."""

    def on_data(self, event) -> None:
        """Place bets on horses whose expected value exceeds the threshold."""

        if event.kind != "race":
            return
        race = event.race
        for horse in race.horses:
            odds = horse.odds.get("win") or horse.odds.get("単勝")
            if odds is None:
                continue
            history = self.get_historical(horse.horse_id)
            win_rate = history.get("win_rate", 0.0)
            expected_value = win_rate * odds
            if expected_value >= self.edge_threshold and self.get_balance() >= self.stake:
                self.place_bet(race.race_id, [horse.horse_id], self.stake, "win")
