"""Pipeline primitives for feature preprocessing."""

from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import only for typing
    import pandas as pd


class PipelineStep(Protocol):
    """Protocol describing a pipeline step."""

    def transform(self, frame: "pd.DataFrame") -> "pd.DataFrame":  # pragma: no cover - interface stub
        """Transform ``frame`` and return the processed dataframe."""


__all__ = ["PipelineStep"]
