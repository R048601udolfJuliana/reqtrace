"""Entry rating — attach a 1-5 star rating and optional comment to a log entry."""

from __future__ import annotations

from typing import Optional

from reqtrace.storage import LogStore

_VALID_RATINGS = frozenset(range(1, 6))
_META_RATING = "rating"
_META_COMMENT = "rating_comment"


class RatingError(ValueError):
    """Raised when an invalid rating value is supplied."""


def set_rating(store: LogStore, entry_id: str, stars: int, comment: str = "") -> None:
    """Attach a star rating (1-5) to *entry_id*, optionally with a comment."""
    if stars not in _VALID_RATINGS:
        raise RatingError(f"Rating must be between 1 and 5, got {stars!r}")
    entry = store.get_by_id(entry_id)
    if entry is None:
        raise KeyError(f"Entry {entry_id!r} not found")
    entry.metadata[_META_RATING] = stars
    if comment:
        entry.metadata[_META_COMMENT] = comment.strip()
    elif _META_COMMENT in entry.metadata:
        del entry.metadata[_META_COMMENT]


def get_rating(entry) -> Optional[int]:
    """Return the star rating for *entry*, or ``None`` if unrated."""
    return entry.metadata.get(_META_RATING)


def get_comment(entry) -> Optional[str]:
    """Return the rating comment for *entry*, or ``None``."""
    return entry.metadata.get(_META_COMMENT)


def clear_rating(store: LogStore, entry_id: str) -> None:
    """Remove the rating (and comment) from *entry_id*."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        raise KeyError(f"Entry {entry_id!r} not found")
    entry.metadata.pop(_META_RATING, None)
    entry.metadata.pop(_META_COMMENT, None)


def list_rated(store: LogStore) -> list:
    """Return all entries that have a rating, sorted by stars descending."""
    rated = [e for e in store.all() if _META_RATING in e.metadata]
    return sorted(rated, key=lambda e: e.metadata[_META_RATING], reverse=True)


def filter_by_min_rating(store: LogStore, min_stars: int) -> list:
    """Return entries whose rating is >= *min_stars*."""
    return [
        e for e in store.all()
        if e.metadata.get(_META_RATING, 0) >= min_stars
    ]
