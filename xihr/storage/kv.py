"""Key-value storage abstractions backed by SQLite, DuckDB, or Redis."""

from __future__ import annotations

from typing import MutableMapping


class KeyValueStore(MutableMapping[str, bytes]):
    """In-memory key-value store used for testing and development."""

    def __init__(self) -> None:
        self._data: dict[str, bytes] = {}

    def __getitem__(self, key: str) -> bytes:
        return self._data[key]

    def __setitem__(self, key: str, value: bytes) -> None:
        self._data[key] = value

    def __delitem__(self, key: str) -> None:
        del self._data[key]

    def __iter__(self):  # pragma: no cover - trivial
        return iter(self._data)

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._data)

    def clear(self) -> None:
        """Remove all entries from the store."""

        self._data.clear()


__all__ = ["KeyValueStore"]
