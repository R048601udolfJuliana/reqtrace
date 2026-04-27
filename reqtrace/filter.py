"""Filtering utilities for log entries."""
from __future__ import annotations

from typing import Callable, Iterable, List, Optional

from reqtrace.models import RequestLogEntry


class FilterCriteria:
    """Holds criteria used to filter log entries."""

    def __init__(
        self,
        method: Optional[str] = None,
        host: Optional[str] = None,
        path_prefix: Optional[str] = None,
        status_code: Optional[int] = None,
        has_response: Optional[bool] = None,
    ) -> None:
        self.method = method.upper() if method else None
        self.host = host
        self.path_prefix = path_prefix
        self.status_code = status_code
        self.has_response = has_response

    def matches(self, entry: RequestLogEntry) -> bool:
        """Return True if *entry* satisfies all specified criteria."""
        if self.method and entry.request.method.upper() != self.method:
            return False
        if self.host and entry.request.host != self.host:
            return False
        if self.path_prefix and not entry.request.path.startswith(self.path_prefix):
            return False
        if self.status_code is not None:
            if entry.response is None or entry.response.status_code != self.status_code:
                return False
        if self.has_response is True and entry.response is None:
            return False
        if self.has_response is False and entry.response is not None:
            return False
        return True


def apply_filter(
    entries: Iterable[RequestLogEntry],
    criteria: FilterCriteria,
) -> List[RequestLogEntry]:
    """Return a list of entries that match *criteria*."""
    return [e for e in entries if criteria.matches(e)]


def build_predicate(
    method: Optional[str] = None,
    host: Optional[str] = None,
    path_prefix: Optional[str] = None,
    status_code: Optional[int] = None,
    has_response: Optional[bool] = None,
) -> Callable[[RequestLogEntry], bool]:
    """Convenience wrapper that returns a plain callable predicate."""
    criteria = FilterCriteria(
        method=method,
        host=host,
        path_prefix=path_prefix,
        status_code=status_code,
        has_response=has_response,
    )
    return criteria.matches
