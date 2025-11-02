"""Utilities for tracking model artifacts and checkpoints."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass(slots=True)
class Artifact:
    """Metadata describing a stored artifact."""

    name: str
    path: Path
    checksum: str | None = None


class ArtifactRegistry:
    """In-memory registry for run artifacts."""

    def __init__(self) -> None:
        self._artifacts: Dict[str, Artifact] = {}

    def register(self, artifact: Artifact) -> None:
        """Register ``artifact`` replacing any existing entry with the same name."""

        self._artifacts[artifact.name] = artifact

    def get(self, name: str) -> Artifact:
        """Return the artifact metadata for ``name``."""

        return self._artifacts[name]

    def clear(self) -> None:
        """Remove all stored artifact metadata."""

        self._artifacts.clear()


__all__ = ["Artifact", "ArtifactRegistry"]
