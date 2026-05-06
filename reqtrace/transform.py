"""Entry transformation utilities — apply mutations to logged request/response data."""

from __future__ import annotations

from typing import Callable, List, Optional

from reqtrace.models import RequestLogEntry


TransformFn = Callable[[RequestLogEntry], RequestLogEntry]


def set_header(entry: RequestLogEntry, name: str, value: str) -> RequestLogEntry:
    """Return a copy of *entry* with *name* header set to *value* on the request."""
    headers = dict(entry.request.headers)
    headers[name] = value
    entry.request.headers = headers
    return entry


def remove_header(entry: RequestLogEntry, name: str) -> RequestLogEntry:
    """Return a copy of *entry* with *name* header removed from the request (case-insensitive)."""
    headers = {
        k: v for k, v in entry.request.headers.items()
        if k.lower() != name.lower()
    }
    entry.request.headers = headers
    return entry


def replace_body(entry: RequestLogEntry, body: Optional[str]) -> RequestLogEntry:
    """Replace the request body with *body*."""
    entry.request.body = body
    return entry


def rewrite_url(entry: RequestLogEntry, old: str, new: str) -> RequestLogEntry:
    """Replace the first occurrence of *old* in the request URL with *new*."""
    entry.request.url = entry.request.url.replace(old, new, 1)
    return entry


def apply_transforms(
    entry: RequestLogEntry,
    transforms: List[TransformFn],
) -> RequestLogEntry:
    """Apply each transform in *transforms* sequentially and return the result."""
    for fn in transforms:
        entry = fn(entry)
    return entry


def build_transform_pipeline(
    set_headers: Optional[dict] = None,
    remove_headers: Optional[List[str]] = None,
    body: Optional[str] = None,
    url_rewrite: Optional[tuple] = None,
) -> List[TransformFn]:
    """Build a list of transform functions from keyword arguments.

    Parameters
    ----------
    set_headers:   mapping of header name -> value to set.
    remove_headers: list of header names to remove.
    body:          replacement body string, or None to skip.
    url_rewrite:   (old, new) pair for URL substitution, or None to skip.
    """
    pipeline: List[TransformFn] = []

    for name, value in (set_headers or {}).items():
        pipeline.append(lambda e, n=name, v=value: set_header(e, n, v))

    for name in (remove_headers or []):
        pipeline.append(lambda e, n=name: remove_header(e, n))

    if body is not None:
        pipeline.append(lambda e, b=body: replace_body(e, b))

    if url_rewrite is not None:
        old, new = url_rewrite
        pipeline.append(lambda e, o=old, n=new: rewrite_url(e, o, n))

    return pipeline
