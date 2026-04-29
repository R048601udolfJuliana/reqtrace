"""Tag management for request log entries."""

from typing import List, Optional
from reqtrace.storage import LogStore


def add_tag(store: LogStore, entry_id: str, tag: str) -> bool:
    """Add a tag to a log entry. Returns True if successful, False if entry not found."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        return False
    tag = tag.strip().lower()
    if not tag:
        raise ValueError("Tag must not be empty")
    if tag not in entry.tags:
        entry.tags.append(tag)
    return True


def remove_tag(store: LogStore, entry_id: str, tag: str) -> bool:
    """Remove a tag from a log entry. Returns True if successful, False if entry not found."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        return False
    tag = tag.strip().lower()
    try:
        entry.tags.remove(tag)
    except ValueError:
        pass
    return True


def get_tags(store: LogStore, entry_id: str) -> Optional[List[str]]:
    """Return tags for a given entry, or None if entry not found."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        return None
    return list(entry.tags)


def filter_by_tag(store: LogStore, tag: str):
    """Return all entries that have the given tag."""
    tag = tag.strip().lower()
    return [e for e in store.all() if tag in e.tags]


def list_all_tags(store: LogStore) -> List[str]:
    """Return a sorted list of all unique tags across all entries."""
    tags = set()
    for entry in store.all():
        tags.update(entry.tags)
    return sorted(tags)
