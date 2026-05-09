"""Severity levels for request log entries."""

from __future__ import annotations

from typing import List

from reqtrace.models import RequestLogEntry
from reqtrace.storage import LogStore

SEVERITY_LEVELS = ("low", "medium", "high", "critical")
_META_KEY = "severity"
_TAG_PREFIX = "severity:"


class SeverityError(Exception):
    """Raised when an invalid severity level is supplied."""


def _validate(level: str) -> str:
    normalised = level.lower().strip()
    if normalised not in SEVERITY_LEVELS:
        raise SeverityError(
            f"Invalid severity '{level}'. Choose from: {', '.join(SEVERITY_LEVELS)}"
        )
    return normalised


def set_severity(entry: RequestLogEntry, level: str) -> None:
    """Attach a severity level to *entry*, replacing any previous value."""
    normalised = _validate(level)
    # Remove any existing severity tag first
    existing_tags = [t for t in entry.metadata.get("tags", []) if not t.startswith(_TAG_PREFIX)]
    existing_tags.append(f"{_TAG_PREFIX}{normalised}")
    entry.metadata["tags"] = existing_tags
    entry.metadata[_META_KEY] = normalised


def get_severity(entry: RequestLogEntry) -> str | None:
    """Return the severity level stored on *entry*, or ``None``."""
    return entry.metadata.get(_META_KEY)


def clear_severity(entry: RequestLogEntry) -> None:
    """Remove the severity level (and related tag) from *entry*."""
    entry.metadata.pop(_META_KEY, None)
    entry.metadata["tags"] = [
        t for t in entry.metadata.get("tags", []) if not t.startswith(_TAG_PREFIX)
    ]


def filter_by_severity(store: LogStore, level: str) -> List[RequestLogEntry]:
    """Return all entries whose severity matches *level*."""
    normalised = _validate(level)
    return [e for e in store.all() if get_severity(e) == normalised]


def list_by_severity(store: LogStore) -> dict[str, List[RequestLogEntry]]:
    """Return a mapping of severity level -> list of matching entries."""
    result: dict[str, List[RequestLogEntry]] = {lvl: [] for lvl in SEVERITY_LEVELS}
    for entry in store.all():
        lvl = get_severity(entry)
        if lvl and lvl in result:
            result[lvl].append(entry)
    return result
