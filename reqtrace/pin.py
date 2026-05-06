"""Pin/unpin entries for quick access and persistent reference."""

from __future__ import annotations

from typing import List

PIN_TAG = "pinned"


def pin_entry(store, entry_id: str) -> bool:
    """Pin an entry by ID. Returns True if entry was found and pinned."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        return False
    tags: List[str] = list(entry.metadata.get("tags", []))
    if PIN_TAG not in tags:
        tags.append(PIN_TAG)
        entry.metadata["tags"] = tags
    entry.metadata["pinned"] = True
    store.update(entry)
    return True


def unpin_entry(store, entry_id: str) -> bool:
    """Unpin an entry by ID. Returns True if entry was found."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        return False
    tags: List[str] = list(entry.metadata.get("tags", []))
    if PIN_TAG in tags:
        tags.remove(PIN_TAG)
        entry.metadata["tags"] = tags
    entry.metadata["pinned"] = False
    store.update(entry)
    return True


def is_pinned(entry) -> bool:
    """Return True if the entry is currently pinned."""
    return bool(entry.metadata.get("pinned", False))


def list_pinned(store) -> list:
    """Return all pinned entries from the store."""
    return [e for e in store.all() if is_pinned(e)]
