"""Naive strategy backing the favourite in every race."""
from __future__ import annotations

from xihr.models import HorseEntry, Race
from xihr.strategy import BaseStrategy


class NaiveFavoriteStrategy(BaseStrategy):
    """Strategy that always backs the lowest-odds runner to win."""

    stake: float = 100.0
    """Stake amount wagered on each race."""

    def on_data(self, event) -> None:
        """Submit a bet for the favourite whenever race data arrives."""

        if event.kind != "race":
            return
        race: Race = event.race
        favourite = self._find_favourite(race)
        if favourite is None:
            return
        self.place_bet(race.race_id, [favourite.horse_id], self.stake, "win")

    def _find_favourite(self, race: Race) -> HorseEntry | None:
        """Return the horse with the lowest available win odds."""

        best: HorseEntry | None = None
        best_odds = float("inf")
        for horse in race.horses:
            odds = horse.odds.get("win") or horse.odds.get("単勝")
            if odds is None:
                continue
            if odds < best_odds:
                best_odds = odds
                best = horse
        return best
