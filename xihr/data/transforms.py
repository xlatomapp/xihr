"""Feature engineering helpers for preparing datasets."""

from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import only for typing
    import polars as pl


class Transform(Protocol):
    """Protocol for stateless dataframe transforms."""

    def apply(self, frame: "pl.DataFrame") -> "pl.DataFrame":  # pragma: no cover - interface stub
        """Apply the transformation to ``frame`` returning a new dataframe."""


__all__ = ["Transform"]
