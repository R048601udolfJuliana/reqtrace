"""Replay recorded HTTP requests for debugging."""

import http.client
import urllib.parse
from typing import Optional

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.storage import LogStore


class ReplayError(Exception):
    """Raised when a replay attempt fails."""


def replay_request(entry: RequestLogEntry, override_host: Optional[str] = None) -> HttpResponse:
    """
    Replay a recorded HTTP request and return the new response.

    Args:
        entry: The log entry containing the original request.
        override_host: Optional host:port to send the request to instead of the original.

    Returns:
        HttpResponse from the replayed request.
    """
    req: HttpRequest = entry.request
    target = override_host or req.host

    parsed = urllib.parse.urlsplit(req.url)
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"

    use_https = parsed.scheme == "https"
    conn_cls = http.client.HTTPSConnection if use_https else http.client.HTTPConnection

    try:
        conn = conn_cls(target, timeout=10)
        headers = dict(req.headers)
        headers["Host"] = target
        body = req.body.encode() if isinstance(req.body, str) else req.body
        conn.request(req.method, path, body=body, headers=headers)
        resp = conn.getresponse()
        resp_body = resp.read().decode("utf-8", errors="replace")
        response_headers = dict(resp.getheaders())
        return HttpResponse(
            status_code=resp.status,
            headers=response_headers,
            body=resp_body,
        )
    except Exception as exc:
        raise ReplayError(f"Failed to replay request {entry.id}: {exc}") from exc
    finally:
        conn.close()


def replay_by_id(store: LogStore, entry_id: str, override_host: Optional[str] = None) -> HttpResponse:
    """Look up a log entry by ID and replay it."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        raise ReplayError(f"No log entry found with id={entry_id!r}")
    return replay_request(entry, override_host=override_host)
