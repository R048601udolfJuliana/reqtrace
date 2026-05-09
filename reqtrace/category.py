"""Category tagging for request log entries.

Allows entries to be assigned a single named category (e.g. 'auth',
'billing', 'search') to aid organisation beyond free-form tags.
"""

from __future__ import annotations

from typing import List, Optional

from reqtrace.models import RequestLogEntry
from reqtrace.storage import LogStore

_META_KEY = "category"


class CategoryError(Exception):
    """Raised when a category operation cannot be completed."""


def _normalise(category: str) -> str:
    value = category.strip().lower()
    if not value:
        raise CategoryError("Category must not be empty.")
    return value


def set_category(entry: RequestLogEntry, category: str) -> None:
    """Assign *category* to *entry*, overwriting any existing value."""
    entry.metadata[_META_KEY] = _normalise(category)


def get_category(entry: RequestLogEntry) -> Optional[str]:
    """Return the category assigned to *entry*, or ``None``."""
    return entry.metadata.get(_META_KEY)


def clear_category(entry: RequestLogEntry) -> None:
    """Remove the category from *entry* if present."""
    entry.metadata.pop(_META_KEY, None)


def filter_by_category(
    store: LogStore, category: str
) -> List[RequestLogEntry]:
    """Return all entries in *store* that belong to *category*."""
    target = _normalise(category)
    return [e for e in store.all() if e.metadata.get(_META_KEY) == target]


def list_categories(store: LogStore) -> List[str]:
    """Return a sorted, deduplicated list of all categories used in *store*."""
    seen: set[str] = set()
    for entry in store.all():
        cat = entry.metadata.get(_META_KEY)
        if cat:
            seen.add(cat)
    return sorted(seen)
