"""Summarize a single RequestLogEntry into a human-readable one-liner or dict."""

from __future__ import annotations

from typing import Optional

from reqtrace.models import RequestLogEntry


_STATUS_LABEL = {
    range(100, 200): "1xx Informational",
    range(200, 300): "2xx Success",
    range(300, 400): "3xx Redirection",
    range(400, 500): "4xx Client Error",
    range(500, 600): "5xx Server Error",
}


def _status_class(code: int) -> str:
    for r, label in _STATUS_LABEL.items():
        if code in r:
            return label
    return "Unknown"


def _body_snippet(body: Optional[str], max_len: int = 60) -> str:
    if not body:
        return "(empty)"
    body = body.strip()
    if len(body) <= max_len:
        return body
    return body[:max_len] + "…"


def summarize_entry(entry: RequestLogEntry) -> dict:
    """Return a concise summary dict for *entry*."""
    req = entry.request
    resp = entry.response

    summary: dict = {
        "id": entry.id,
        "timestamp": entry.timestamp,
        "method": req.method,
        "url": req.url,
        "request_body_snippet": _body_snippet(req.body),
        "tags": list(entry.tags) if entry.tags else [],
    }

    if resp is not None:
        summary["status_code"] = resp.status_code
        summary["status_class"] = _status_class(resp.status_code)
        summary["response_body_snippet"] = _body_snippet(resp.body)
    else:
        summary["status_code"] = None
        summary["status_class"] = "No Response"
        summary["response_body_snippet"] = "(no response)"

    return summary


def format_summary(entry: RequestLogEntry) -> str:
    """Return a single human-readable summary line for *entry*."""
    s = summarize_entry(entry)
    status_part = (
        f"HTTP {s['status_code']} ({s['status_class']})"
        if s["status_code"] is not None
        else "No Response"
    )
    tags_part = f" [{', '.join(s['tags'])}]" if s["tags"] else ""
    return (
        f"[{s['id'][:8]}] {s['timestamp']}  "
        f"{s['method']} {s['url']}  →  {status_part}{tags_part}"
    )
