"""Common type aliases and enumerations used across the engine."""

from __future__ import annotations

from enum import Enum
from typing import Literal, Protocol, TypeVar


class MarketPhase(str, Enum):
    """Enumerates the discrete phases the engine can operate in."""

    PRE_OPEN = "pre_open"
    OPEN = "open"
    CLOSED = "closed"


class SupportsID(Protocol):
    """Protocol for objects that expose a string identifier via ``id`` attribute."""

    id: str


BetKind = Literal[
    "win",
    "place",
    "bracket_quinella",
    "quinella",
    "exacta",
    "quinella_place",
    "trifecta_box",
    "trifecta_exact",
]
"""Canonical betting market identifiers used by execution components."""

PayloadT = TypeVar("PayloadT")
"""Generic payload type for messaging primitives."""

__all__ = ["MarketPhase", "SupportsID", "BetKind", "PayloadT"]
