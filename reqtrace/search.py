"""Full-text and field search helpers built on top of filter.py."""
from __future__ import annotations

from typing import List, Optional

from reqtrace.models import RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.filter import FilterCriteria, apply_filter


def search_store(
    store: LogStore,
    *,
    method: Optional[str] = None,
    host: Optional[str] = None,
    path_prefix: Optional[str] = None,
    status_code: Optional[int] = None,
    has_response: Optional[bool] = None,
    body_contains: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[RequestLogEntry]:
    """Search *store* using the supplied criteria and return matching entries.

    Parameters
    ----------
    store:          The :class:`LogStore` to search.
    method:         HTTP method to match (case-insensitive).
    host:           Exact host to match.
    path_prefix:    Path prefix to match.
    status_code:    Response status code to match.
    has_response:   If True/False, filter on whether a response is present.
    body_contains:  Substring that must appear in the *request* body.
    limit:          Maximum number of results to return.
    """
    criteria = FilterCriteria(
        method=method,
        host=host,
        path_prefix=path_prefix,
        status_code=status_code,
        has_response=has_response,
    )

    candidates = apply_filter(store.all(), criteria)

    if body_contains is not None:
        needle = body_contains
        candidates = [
            e for e in candidates
            if e.request.body is not None and needle in e.request.body
        ]

    if limit is not None:
        candidates = candidates[:limit]

    return candidates


def search_by_body(
    store: LogStore,
    substring: str,
    limit: Optional[int] = None,
) -> List[RequestLogEntry]:
    """Shortcut: find entries whose request body contains *substring*."""
    return search_store(store, body_contains=substring, limit=limit)
