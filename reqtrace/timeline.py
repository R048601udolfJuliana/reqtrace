"""Timeline view: sort and bucket log entries by time."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from reqtrace.models import RequestLogEntry


def _parse_ts(entry: RequestLogEntry) -> datetime:
    """Return a timezone-aware datetime from the entry timestamp string."""
    ts = entry.timestamp
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def sort_entries(
    entries: List[RequestLogEntry],
    descending: bool = False,
) -> List[RequestLogEntry]:
    """Return entries sorted chronologically."""
    return sorted(entries, key=_parse_ts, reverse=descending)


def bucket_by_minute(
    entries: List[RequestLogEntry],
) -> Dict[str, List[RequestLogEntry]]:
    """Group entries into buckets keyed by 'YYYY-MM-DDTHH:MM' (UTC)."""
    buckets: Dict[str, List[RequestLogEntry]] = {}
    for entry in entries:
        dt = _parse_ts(entry).astimezone(timezone.utc)
        key = dt.strftime("%Y-%m-%dT%H:%M")
        buckets.setdefault(key, []).append(entry)
    return buckets


def format_timeline(
    entries: List[RequestLogEntry],
    descending: bool = False,
) -> str:
    """Return a human-readable timeline string."""
    sorted_entries = sort_entries(entries, descending=descending)
    if not sorted_entries:
        return "No entries."

    lines: List[str] = []
    buckets = bucket_by_minute(sorted_entries)
    # Preserve bucket order from sorted entries
    seen: List[str] = []
    for entry in sorted_entries:
        dt = _parse_ts(entry).astimezone(timezone.utc)
        key = dt.strftime("%Y-%m-%dT%H:%M")
        if key not in seen:
            seen.append(key)

    for key in seen:
        lines.append(f"[{key}]")
        for e in buckets[key]:
            status = (
                str(e.response.status_code) if e.response else "---"
            )
            lines.append(
                f"  {e.id[:8]}  {e.request.method:<6} {e.request.url}  -> {status}"
            )
    return "\n".join(lines)
