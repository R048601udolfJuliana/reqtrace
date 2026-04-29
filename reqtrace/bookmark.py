"""Bookmark (favourite) log entries for quick retrieval."""

from __future__ import annotations

from typing import List

from reqtrace.models import RequestLogEntry
from reqtrace.storage import LogStore

_BOOKMARK_TAG = "__bookmarked__"


def bookmark_entry(store: LogStore, entry_id: str) -> RequestLogEntry:
    """Mark an entry as bookmarked. Returns the updated entry."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        raise KeyError(f"Entry {entry_id!r} not found")
    tags: List[str] = list(entry.tags) if entry.tags else []
    if _BOOKMARK_TAG not in tags:
        tags.append(_BOOKMARK_TAG)
        entry.tags = tags
        store.update(entry)
    return entry


def unbookmark_entry(store: LogStore, entry_id: str) -> RequestLogEntry:
    """Remove the bookmark from an entry. Returns the updated entry."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        raise KeyError(f"Entry {entry_id!r} not found")
    tags: List[str] = list(entry.tags) if entry.tags else []
    if _BOOKMARK_TAG in tags:
        tags.remove(_BOOKMARK_TAG)
        entry.tags = tags
        store.update(entry)
    return entry


def is_bookmarked(entry: RequestLogEntry) -> bool:
    """Return True if the entry is bookmarked."""
    return _BOOKMARK_TAG in (entry.tags or [])


def list_bookmarks(store: LogStore) -> List[RequestLogEntry]:
    """Return all bookmarked entries in insertion order."""
    return [e for e in store.all() if is_bookmarked(e)]
