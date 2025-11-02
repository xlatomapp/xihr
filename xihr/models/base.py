"""Base interfaces for machine learning models."""

from __future__ import annotations

from typing import Protocol, Sequence, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import only for typing
    import pandas as pd


class MLModel(Protocol):
    """Protocol describing the minimal model lifecycle."""

    def fit(self, features: "pd.DataFrame", targets: Sequence[float]) -> None:  # pragma: no cover - interface stub
        """Train the model using ``features`` and ``targets``."""

    def predict(self, features: "pd.DataFrame") -> Sequence[float]:  # pragma: no cover - interface stub
        """Return predictions for ``features``."""

    def rank(self, features: "pd.DataFrame") -> Sequence[int]:  # pragma: no cover - interface stub
        """Return ranking indices for ``features``."""


__all__ = ["MLModel"]
