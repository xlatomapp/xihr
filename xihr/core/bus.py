"""Simple publish/subscribe event bus primitives."""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, DefaultDict, Generic, Iterable, List, TypeVar

EventT = TypeVar("EventT")


class EventBus(Generic[EventT]):
    """Minimal in-memory pub/sub bus used by the engine."""

    def __init__(self) -> None:
        self._subscribers: DefaultDict[str, List[Callable[[EventT], None]]] = defaultdict(list)

    def subscribe(self, topic: str, callback: Callable[[EventT], None]) -> None:
        """Register ``callback`` to receive events published on ``topic``."""

        self._subscribers[topic].append(callback)

    def publish(self, topic: str, event: EventT) -> None:
        """Send ``event`` to all subscribers registered for ``topic``."""

        for handler in list(self._subscribers.get(topic, [])):
            handler(event)

    def topics(self) -> Iterable[str]:
        """Return the set of topics with at least one subscriber."""

        return self._subscribers.keys()

    def clear(self) -> None:
        """Remove all registered subscribers."""

        self._subscribers.clear()


__all__ = ["EventBus"]
