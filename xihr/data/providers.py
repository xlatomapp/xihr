"""Live data provider interfaces and adapters."""

from __future__ import annotations

from typing import Protocol

from .models import Race


class OddsProvider(Protocol):
    """Protocol for components able to stream live odds."""

    def subscribe(self, race: Race) -> None:  # pragma: no cover - interface stub
        """Begin streaming odds updates for ``race``."""

    def unsubscribe(self, race: Race) -> None:  # pragma: no cover - interface stub
        """Stop streaming odds updates for ``race``."""


__all__ = ["OddsProvider"]
