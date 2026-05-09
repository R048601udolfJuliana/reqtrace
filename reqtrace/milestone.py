"""Milestone tracking for request log entries."""

from __future__ import annotations

from typing import List, Optional

MILESTONE_KEY = "milestone"
MILESTONE_REACHED_KEY = "milestone_reached"


class MilestoneError(Exception):
    """Raised when a milestone operation fails."""


def set_milestone(store, entry_id: str, name: str, reached: bool = False) -> None:
    """Attach a milestone name to an entry."""
    name = name.strip()
    if not name:
        raise MilestoneError("Milestone name must not be empty.")
    entry = store.get_by_id(entry_id)
    if entry is None:
        raise MilestoneError(f"Entry '{entry_id}' not found.")
    entry.metadata[MILESTONE_KEY] = name
    entry.metadata[MILESTONE_REACHED_KEY] = reached


def get_milestone(store, entry_id: str) -> Optional[str]:
    """Return the milestone name for an entry, or None."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        return None
    return entry.metadata.get(MILESTONE_KEY)


def is_reached(store, entry_id: str) -> bool:
    """Return True if the milestone has been marked as reached."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        return False
    return bool(entry.metadata.get(MILESTONE_REACHED_KEY, False))


def mark_reached(store, entry_id: str) -> None:
    """Mark the milestone on an entry as reached."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        raise MilestoneError(f"Entry '{entry_id}' not found.")
    if MILESTONE_KEY not in entry.metadata:
        raise MilestoneError(f"Entry '{entry_id}' has no milestone set.")
    entry.metadata[MILESTONE_REACHED_KEY] = True


def clear_milestone(store, entry_id: str) -> None:
    """Remove milestone metadata from an entry."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        raise MilestoneError(f"Entry '{entry_id}' not found.")
    entry.metadata.pop(MILESTONE_KEY, None)
    entry.metadata.pop(MILESTONE_REACHED_KEY, None)


def list_milestones(store) -> List[dict]:
    """Return a list of dicts describing all entries that have a milestone."""
    results = []
    for entry in store.all():
        name = entry.metadata.get(MILESTONE_KEY)
        if name is not None:
            results.append({
                "id": entry.id,
                "milestone": name,
                "reached": bool(entry.metadata.get(MILESTONE_REACHED_KEY, False)),
            })
    return results
