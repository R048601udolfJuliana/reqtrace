"""Anonymization utilities for scrubbing sensitive data from request log entries."""

import re
from typing import Dict, List, Optional
from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry

DEFAULT_SENSITIVE_HEADERS = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-auth-token",
    "proxy-authorization",
}

REDACTED = "[REDACTED]"


def _scrub_headers(headers: Dict[str, str], sensitive: set) -> Dict[str, str]:
    """Return a copy of headers with sensitive values replaced."""
    return {
        k: (REDACTED if k.lower() in sensitive else v)
        for k, v in headers.items()
    }


def _scrub_body(body: Optional[str], patterns: List[re.Pattern]) -> Optional[str]:
    """Replace pattern matches in body with REDACTED."""
    if body is None:
        return None
    for pattern in patterns:
        body = pattern.sub(REDACTED, body)
    return body


def anonymize_entry(
    entry: RequestLogEntry,
    sensitive_headers: Optional[set] = None,
    body_patterns: Optional[List[str]] = None,
) -> RequestLogEntry:
    """Return a new RequestLogEntry with sensitive data scrubbed."""
    if sensitive_headers is None:
        sensitive_headers = DEFAULT_SENSITIVE_HEADERS
    compiled = [re.compile(p) for p in (body_patterns or [])]

    req = entry.request
    clean_request = HttpRequest(
        method=req.method,
        url=req.url,
        headers=_scrub_headers(req.headers, sensitive_headers),
        body=_scrub_body(req.body, compiled),
    )

    clean_response = None
    if entry.response is not None:
        resp = entry.response
        clean_response = HttpResponse(
            status_code=resp.status_code,
            headers=_scrub_headers(resp.headers, sensitive_headers),
            body=_scrub_body(resp.body, compiled),
            elapsed_ms=resp.elapsed_ms,
        )

    return RequestLogEntry(
        request=clean_request,
        response=clean_response,
        id=entry.id,
        timestamp=entry.timestamp,
    )
