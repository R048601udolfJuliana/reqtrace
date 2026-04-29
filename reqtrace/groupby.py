"""Group log entries by a specified field for analysis."""

from collections import defaultdict
from typing import Callable, Dict, List

from reqtrace.models import RequestLogEntry
from reqtrace.storage import LogStore


GROUP_BY_FIELDS = ("method", "host", "status", "path")


def _get_host(entry: RequestLogEntry) -> str:
    from urllib.parse import urlparse
    return urlparse(entry.request.url).netloc or "unknown"


def _get_path(entry: RequestLogEntry) -> str:
    from urllib.parse import urlparse
    return urlparse(entry.request.url).path or "/"


def _get_status(entry: RequestLogEntry) -> str:
    if entry.response is None:
        return "no_response"
    return str(entry.response.status_code)


def _get_method(entry: RequestLogEntry) -> str:
    return entry.request.method.upper()


_EXTRACTORS: Dict[str, Callable[[RequestLogEntry], str]] = {
    "method": _get_method,
    "host": _get_host,
    "status": _get_status,
    "path": _get_path,
}


def group_entries(
    entries: List[RequestLogEntry], field: str
) -> Dict[str, List[RequestLogEntry]]:
    """Group a list of entries by the given field name.

    Args:
        entries: List of RequestLogEntry objects to group.
        field: One of 'method', 'host', 'status', 'path'.

    Returns:
        A dict mapping group key -> list of entries.

    Raises:
        ValueError: If the field is not supported.
    """
    if field not in _EXTRACTORS:
        raise ValueError(
            f"Unsupported group-by field '{field}'. "
            f"Choose from: {', '.join(GROUP_BY_FIELDS)}"
        )
    extractor = _EXTRACTORS[field]
    groups: Dict[str, List[RequestLogEntry]] = defaultdict(list)
    for entry in entries:
        key = extractor(entry)
        groups[key].append(entry)
    return dict(groups)


def group_store(store: LogStore, field: str) -> Dict[str, List[RequestLogEntry]]:
    """Convenience wrapper that groups all entries in a LogStore."""
    return group_entries(store.all(), field)


def format_groups(groups: Dict[str, List[RequestLogEntry]]) -> str:
    """Return a human-readable summary of grouped entries."""
    if not groups:
        return "No entries to group."
    lines = []
    for key in sorted(groups):
        count = len(groups[key])
        lines.append(f"{key}: {count} entr{'y' if count == 1 else 'ies'}")
    return "\n".join(lines)
