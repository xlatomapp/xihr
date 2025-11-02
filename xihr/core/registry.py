"""Lightweight registries for strategies, models, and providers."""

from __future__ import annotations

from typing import Dict, Generic, Iterable, Iterator, TypeVar

T = TypeVar("T")


class Registry(Generic[T]):
    """Simple name-to-object registry."""

    def __init__(self) -> None:
        self._items: Dict[str, T] = {}

    def register(self, name: str, item: T) -> None:
        """Register ``item`` under ``name`` replacing any existing entry."""

        self._items[name] = item

    def get(self, name: str) -> T:
        """Return the registered item for ``name``."""

        return self._items[name]

    def __contains__(self, name: object) -> bool:
        return name in self._items

    def __iter__(self) -> Iterator[tuple[str, T]]:
        return iter(self._items.items())

    def values(self) -> Iterable[T]:
        """Iterate over registered items."""

        return self._items.values()

    def clear(self) -> None:
        """Remove all registered items."""

        self._items.clear()


__all__ = ["Registry"]
