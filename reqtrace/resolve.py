"""Resolve and validate URLs stored in request log entries."""

from __future__ import annotations

import socket
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from reqtrace.storage import LogStore


@dataclass
class ResolveResult:
    entry_id: str
    url: str
    host: str
    resolved_ips: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None and bool(self.resolved_ips)

    def summary(self) -> str:
        if self.error:
            return f"[FAIL] {self.url} — {self.error}"
        ips = ", ".join(self.resolved_ips)
        return f"[OK]   {self.url} — {self.host} -> {ips}"


def _extract_host(url: str) -> Optional[str]:
    """Return the hostname from a URL string, or None if unparseable."""
    try:
        parsed = urlparse(url)
        return parsed.hostname or None
    except Exception:
        return None


def resolve_url(entry_id: str, url: str) -> ResolveResult:
    """Attempt DNS resolution for the host in *url*."""
    host = _extract_host(url)
    if not host:
        return ResolveResult(
            entry_id=entry_id,
            url=url,
            host="",
            error=f"Cannot extract host from URL: {url!r}",
        )
    try:
        infos = socket.getaddrinfo(host, None)
        ips = list({info[4][0] for info in infos})
        return ResolveResult(entry_id=entry_id, url=url, host=host, resolved_ips=ips)
    except socket.gaierror as exc:
        return ResolveResult(
            entry_id=entry_id,
            url=url,
            host=host,
            error=str(exc),
        )


def resolve_store(
    store: LogStore,
    entry_id: Optional[str] = None,
) -> List[ResolveResult]:
    """Resolve URLs for all entries (or a single entry) in *store*."""
    if entry_id is not None:
        entry = store.get_by_id(entry_id)
        if entry is None:
            return []
        entries = [entry]
    else:
        entries = store.all()

    results: List[ResolveResult] = []
    for entry in entries:
        url = entry.request.url
        results.append(resolve_url(entry.id, url))
    return results
