"""Archive and unarchive log entries to keep the active store clean."""

from __future__ import annotations

from typing import List

ARCHIVED_TAG = "archived"


def archive_entry(store, entry_id: str) -> bool:
    """Mark an entry as archived. Returns True if the entry was found."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        return False
    tags: list = entry.metadata.setdefault("tags", [])
    if ARCHIVED_TAG not in tags:
        tags.append(ARCHIVED_TAG)
    entry.metadata["archived"] = True
    store.update(entry)
    return True


def unarchive_entry(store, entry_id: str) -> bool:
    """Remove the archived mark from an entry. Returns True if the entry was found."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        return False
    tags: list = entry.metadata.get("tags", [])
    entry.metadata["tags"] = [t for t in tags if t != ARCHIVED_TAG]
    entry.metadata.pop("archived", None)
    store.update(entry)
    return True


def is_archived(entry) -> bool:
    """Return True if the entry is currently archived."""
    return bool(entry.metadata.get("archived", False))


def list_archived(store) -> List:
    """Return all archived entries."""
    return [e for e in store.all() if is_archived(e)]


def list_active(store) -> List:
    """Return all non-archived entries."""
    return [e for e in store.all() if not is_archived(e)]


def purge_archived(store) -> int:
    """Permanently delete all archived entries. Returns the count removed."""
    to_remove = list_archived(store)
    for entry in to_remove:
        store.delete(entry.id)
    return len(to_remove)
