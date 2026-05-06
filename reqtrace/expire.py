"""Expiry management for log entries.

Allows entries to be marked with a TTL (time-to-live) and provides
utilities to identify and purge expired entries from a store.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List, Optional

from reqtrace.models import RequestLogEntry
from reqtrace.storage import LogStore

_EXPIRE_AT_KEY = "expire_at"  # ISO-8601 string stored in metadata


def set_expiry(entry: RequestLogEntry, ttl_seconds: int) -> RequestLogEntry:
    """Set an expiry time on *entry* relative to now.

    Args:
        entry: The log entry to annotate.
        ttl_seconds: Seconds from now after which the entry is considered expired.

    Returns:
        The same entry (mutated in place) for convenience.

    Raises:
        ValueError: If *ttl_seconds* is not a positive integer.
    """
    if ttl_seconds <= 0:
        raise ValueError("ttl_seconds must be a positive integer")
    expire_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    entry.metadata[_EXPIRE_AT_KEY] = expire_at.isoformat()
    return entry


def get_expiry(entry: RequestLogEntry) -> Optional[datetime]:
    """Return the expiry datetime for *entry*, or ``None`` if not set."""
    raw = entry.metadata.get(_EXPIRE_AT_KEY)
    if raw is None:
        return None
    return datetime.fromisoformat(raw)


def is_expired(entry: RequestLogEntry, *, now: Optional[datetime] = None) -> bool:
    """Return ``True`` if *entry* has passed its expiry time."""
    expiry = get_expiry(entry)
    if expiry is None:
        return False
    if now is None:
        now = datetime.now(timezone.utc)
    return now >= expiry


def clear_expiry(entry: RequestLogEntry) -> RequestLogEntry:
    """Remove the expiry annotation from *entry*."""
    entry.metadata.pop(_EXPIRE_AT_KEY, None)
    return entry


def list_expired(store: LogStore, *, now: Optional[datetime] = None) -> List[RequestLogEntry]:
    """Return all entries in *store* that have expired."""
    return [e for e in store.all() if is_expired(e, now=now)]


def purge_expired(store: LogStore, *, now: Optional[datetime] = None) -> int:
    """Delete all expired entries from *store*.

    Returns:
        The number of entries removed.
    """
    expired = list_expired(store, now=now)
    for entry in expired:
        store.delete(entry.id)
    return len(expired)
