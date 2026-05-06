"""Flag entries for follow-up review."""
from __future__ import annotations

from typing import List

from reqtrace.models import RequestLogEntry
from reqtrace.storage import LogStore

_FLAG_TAG = "flagged"
_META_KEY = "flagged"
_REASON_KEY = "flag_reason"


def flag_entry(store: LogStore, entry_id: str, reason: str = "") -> RequestLogEntry:
    """Mark an entry as flagged, optionally storing a reason."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        raise KeyError(f"Entry not found: {entry_id}")
    entry.metadata[_META_KEY] = True
    if reason:
        entry.metadata[_REASON_KEY] = reason.strip()
    tags: List[str] = entry.metadata.get("tags", [])
    if _FLAG_TAG not in tags:
        tags.append(_FLAG_TAG)
    entry.metadata["tags"] = tags
    store.add(entry)
    return entry


def unflag_entry(store: LogStore, entry_id: str) -> RequestLogEntry:
    """Remove the flagged status from an entry."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        raise KeyError(f"Entry not found: {entry_id}")
    entry.metadata.pop(_META_KEY, None)
    entry.metadata.pop(_REASON_KEY, None)
    tags: List[str] = entry.metadata.get("tags", [])
    entry.metadata["tags"] = [t for t in tags if t != _FLAG_TAG]
    store.add(entry)
    return entry


def is_flagged(entry: RequestLogEntry) -> bool:
    """Return True if the entry is currently flagged."""
    return bool(entry.metadata.get(_META_KEY, False))


def get_flag_reason(entry: RequestLogEntry) -> str:
    """Return the flag reason, or empty string if none."""
    return entry.metadata.get(_REASON_KEY, "")


def list_flagged(store: LogStore) -> List[RequestLogEntry]:
    """Return all flagged entries from the store."""
    return [e for e in store.all() if is_flagged(e)]
