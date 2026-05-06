"""Label management for request log entries.

Labels are short, human-readable identifiers (e.g. 'auth-flow', 'bug-123')
stored in entry metadata under the 'labels' key.
"""

from __future__ import annotations

from typing import List

from reqtrace.storage import LogStore

_META_KEY = "labels"


def _normalise(label: str) -> str:
    return label.strip().lower().replace(" ", "-")


def add_label(store: LogStore, entry_id: str, label: str) -> None:
    """Attach *label* to the entry identified by *entry_id*."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        raise KeyError(f"Entry not found: {entry_id}")
    label = _normalise(label)
    labels: List[str] = entry.metadata.setdefault(_META_KEY, [])
    if label not in labels:
        labels.append(label)
    store.update(entry)


def remove_label(store: LogStore, entry_id: str, label: str) -> None:
    """Remove *label* from the entry identified by *entry_id*."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        raise KeyError(f"Entry not found: {entry_id}")
    label = _normalise(label)
    labels: List[str] = entry.metadata.get(_META_KEY, [])
    entry.metadata[_META_KEY] = [l for l in labels if l != label]
    store.update(entry)


def get_labels(store: LogStore, entry_id: str) -> List[str]:
    """Return all labels attached to *entry_id*."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        raise KeyError(f"Entry not found: {entry_id}")
    return list(entry.metadata.get(_META_KEY, []))


def filter_by_label(store: LogStore, label: str):
    """Return all entries that carry *label*."""
    label = _normalise(label)
    return [
        e for e in store.all()
        if label in e.metadata.get(_META_KEY, [])
    ]


def list_all_labels(store: LogStore) -> List[str]:
    """Return a sorted, deduplicated list of every label in the store."""
    seen: set = set()
    for entry in store.all():
        for lbl in entry.metadata.get(_META_KEY, []):
            seen.add(lbl)
    return sorted(seen)
