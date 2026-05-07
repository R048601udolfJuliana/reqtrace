"""Reminder/follow-up scheduling for logged request entries."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List, Optional

from reqtrace.models import RequestLogEntry
from reqtrace.storage import LogStore

_REMIND_AT_KEY = "remind_at"
_REMIND_NOTE_KEY = "remind_note"


class ReminderError(Exception):
    """Raised when a reminder operation fails."""


def set_reminder(
    store: LogStore,
    entry_id: str,
    minutes: int,
    note: str = "",
) -> RequestLogEntry:
    """Schedule a reminder for *entry_id* in *minutes* minutes from now."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        raise ReminderError(f"Entry not found: {entry_id}")
    if minutes <= 0:
        raise ReminderError("minutes must be a positive integer")

    remind_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    entry.metadata[_REMIND_AT_KEY] = remind_at.isoformat()
    if note:
        entry.metadata[_REMIND_NOTE_KEY] = note.strip()
    elif _REMIND_NOTE_KEY in entry.metadata:
        del entry.metadata[_REMIND_NOTE_KEY]
    store.update(entry)
    return entry


def clear_reminder(store: LogStore, entry_id: str) -> RequestLogEntry:
    """Remove any scheduled reminder from *entry_id*."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        raise ReminderError(f"Entry not found: {entry_id}")
    entry.metadata.pop(_REMIND_AT_KEY, None)
    entry.metadata.pop(_REMIND_NOTE_KEY, None)
    store.update(entry)
    return entry


def get_reminder(entry: RequestLogEntry) -> Optional[datetime]:
    """Return the reminder datetime for *entry*, or ``None`` if unset."""
    raw = entry.metadata.get(_REMIND_AT_KEY)
    if raw is None:
        return None
    return datetime.fromisoformat(raw)


def is_due(entry: RequestLogEntry) -> bool:
    """Return ``True`` when the entry has a reminder that is past due."""
    remind_at = get_reminder(entry)
    if remind_at is None:
        return False
    return datetime.now(timezone.utc) >= remind_at


def list_due(store: LogStore) -> List[RequestLogEntry]:
    """Return all entries whose reminders are currently due."""
    return [e for e in store.all() if is_due(e)]
