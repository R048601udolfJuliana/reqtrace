"""Priority tagging for request log entries.

Allows entries to be assigned a numeric priority level (1=low, 2=medium,
3=high) for triage workflows.
"""

from __future__ import annotations

from typing import List

from reqtrace.models import RequestLogEntry
from reqtrace.storage import LogStore

LOW = 1
MEDIUM = 2
HIGH = 3

_VALID = {LOW, MEDIUM, HIGH}
_LABEL_MAP = {LOW: "low", MEDIUM: "medium", HIGH: "high"}
_NAME_MAP = {v: k for k, v in _LABEL_MAP.items()}


class PriorityError(ValueError):
    """Raised when an invalid priority value is supplied."""


def _validate(level: int) -> None:
    if level not in _VALID:
        raise PriorityError(
            f"Invalid priority {level!r}. Must be one of {sorted(_VALID)}."
        )


def set_priority(store: LogStore, entry_id: str, level: int) -> RequestLogEntry:
    """Set the priority level on an entry. Returns the updated entry."""
    _validate(level)
    entry = store.get_by_id(entry_id)
    if entry is None:
        raise KeyError(f"Entry {entry_id!r} not found.")
    entry.metadata["priority"] = level
    return entry


def get_priority(entry: RequestLogEntry) -> int | None:
    """Return the priority level stored on *entry*, or ``None`` if unset."""
    return entry.metadata.get("priority")


def priority_label(entry: RequestLogEntry) -> str:
    """Return a human-readable label for the entry's priority, or ``'none'``."""
    level = get_priority(entry)
    if level is None:
        return "none"
    return _LABEL_MAP.get(level, "unknown")


def filter_by_priority(entries: List[RequestLogEntry], level: int) -> List[RequestLogEntry]:
    """Return only entries whose priority matches *level*."""
    _validate(level)
    return [e for e in entries if get_priority(e) == level]


def list_by_priority(store: LogStore) -> List[RequestLogEntry]:
    """Return all entries that have a priority set, sorted high→low."""
    entries = [e for e in store.all() if get_priority(e) is not None]
    return sorted(entries, key=lambda e: get_priority(e), reverse=True)  # type: ignore[arg-type]
