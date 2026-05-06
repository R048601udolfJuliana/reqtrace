"""Truncate large request/response bodies in log entries for compact display."""

from __future__ import annotations

from typing import Optional

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry

DEFAULT_MAX_BODY_BYTES = 512
_TRUNCATION_MARKER = "...[truncated]"


def _truncate_body(body: Optional[str], max_bytes: int) -> Optional[str]:
    """Return body truncated to *max_bytes* characters, appending a marker."""
    if body is None:
        return None
    if len(body) <= max_bytes:
        return body
    return body[:max_bytes] + _TRUNCATION_MARKER


def truncate_request(req: HttpRequest, max_bytes: int = DEFAULT_MAX_BODY_BYTES) -> HttpRequest:
    """Return a new HttpRequest with its body truncated."""
    return HttpRequest(
        method=req.method,
        url=req.url,
        headers=dict(req.headers),
        body=_truncate_body(req.body, max_bytes),
    )


def truncate_response(resp: HttpResponse, max_bytes: int = DEFAULT_MAX_BODY_BYTES) -> HttpResponse:
    """Return a new HttpResponse with its body truncated."""
    return HttpResponse(
        status_code=resp.status_code,
        headers=dict(resp.headers),
        body=_truncate_body(resp.body, max_bytes),
    )


def truncate_entry(
    entry: RequestLogEntry,
    max_bytes: int = DEFAULT_MAX_BODY_BYTES,
) -> RequestLogEntry:
    """Return a shallow copy of *entry* with request and response bodies truncated.

    The original entry is **not** modified.
    """
    new_entry = RequestLogEntry(
        request=truncate_request(entry.request, max_bytes),
        response=(
            truncate_response(entry.response, max_bytes)
            if entry.response is not None
            else None
        ),
    )
    # Preserve identity fields so the copy is traceable back to the original.
    new_entry.id = entry.id
    new_entry.timestamp = entry.timestamp
    if hasattr(entry, "tags"):
        new_entry.tags = list(entry.tags)
    if hasattr(entry, "notes"):
        new_entry.notes = list(entry.notes)
    return new_entry


def is_truncated(text: Optional[str]) -> bool:
    """Return True if *text* ends with the truncation marker."""
    return text is not None and text.endswith(_TRUNCATION_MARKER)
