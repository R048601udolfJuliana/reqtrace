"""In-memory log store for HTTP request/response entries."""

from __future__ import annotations

from typing import Callable, Iterator, Optional

from reqtrace.models import RequestLogEntry


class LogStore:
    """Thread-unsafe in-memory store for RequestLogEntry objects."""

    def __init__(self) -> None:
        self._entries: dict[str, RequestLogEntry] = {}
        self._order: list[str] = []

    def add(self, entry: RequestLogEntry) -> None:
        """Add a new entry; raises ValueError if ID already exists."""
        if entry.id in self._entries:
            raise ValueError(f"Entry with id {entry.id!r} already exists")
        self._entries[entry.id] = entry
        self._order.append(entry.id)

    def get_by_id(self, entry_id: str) -> Optional[RequestLogEntry]:
        """Return entry by ID or None."""
        return self._entries.get(entry_id)

    def all(self) -> list[RequestLogEntry]:
        """Return all entries in insertion order."""
        return [self._entries[eid] for eid in self._order]

    def update(self, entry: RequestLogEntry) -> None:
        """Replace an existing entry in-place; raises KeyError if not found."""
        if entry.id not in self._entries:
            raise KeyError(f"Entry not found: {entry.id!r}")
        self._entries[entry.id] = entry

    def delete(self, entry_id: str) -> None:
        """Remove an entry by ID; raises KeyError if not found."""
        if entry_id not in self._entries:
            raise KeyError(f"Entry not found: {entry_id!r}")
        del self._entries[entry_id]
        self._order.remove(entry_id)

    def filter(self, predicate: Callable[[RequestLogEntry], bool]) -> list[RequestLogEntry]:
        """Return entries matching predicate."""
        return [e for e in self.all() if predicate(e)]

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self) -> Iterator[RequestLogEntry]:
        return iter(self.all())
