"""Deduplication utilities for request log entries."""

from __future__ import annotations

from typing import List, Optional

from reqtrace.models import RequestLogEntry


def _entry_fingerprint(entry: RequestLogEntry) -> str:
    """Return a string fingerprint for an entry based on method, URL, and body."""
    req = entry.request
    method = req.method.upper()
    url = req.url.rstrip("/")
    body = (req.body or "").strip()
    return f"{method}|{url}|{body}"


def find_duplicates(
    entries: List[RequestLogEntry],
) -> dict[str, List[RequestLogEntry]]:
    """Group entries by fingerprint; return only groups with more than one entry.

    Returns a dict mapping fingerprint -> list of duplicate entries.
    """
    groups: dict[str, List[RequestLogEntry]] = {}
    for entry in entries:
        fp = _entry_fingerprint(entry)
        groups.setdefault(fp, []).append(entry)
    return {fp: members for fp, members in groups.items() if len(members) > 1}


def deduplicate(
    entries: List[RequestLogEntry],
    keep: str = "first",
) -> List[RequestLogEntry]:
    """Return a deduplicated list of entries.

    Args:
        entries: The full list of log entries.
        keep: Either ``'first'`` (default) or ``'last'`` — which copy to retain
              when duplicates are found.

    Returns:
        A new list with duplicates removed, preserving original order of kept
        entries.
    """
    if keep not in ("first", "last"):
        raise ValueError("keep must be 'first' or 'last'")

    seen: dict[str, RequestLogEntry] = {}
    for entry in entries:
        fp = _entry_fingerprint(entry)
        if fp not in seen or keep == "last":
            seen[fp] = entry

    # Preserve the original relative order of the kept entries.
    kept_ids = {e.id for e in seen.values()}
    return [e for e in entries if e.id in kept_ids]


def dedupe_store(store, keep: str = "first") -> int:
    """Remove duplicate entries from *store* in-place.

    Returns the number of entries removed.
    """
    all_entries = store.all()
    deduped = deduplicate(all_entries, keep=keep)
    removed_ids = {e.id for e in all_entries} - {e.id for e in deduped}
    for eid in removed_ids:
        store.delete(eid)
    return len(removed_ids)
