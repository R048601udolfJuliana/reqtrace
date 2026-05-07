"""Tests for reqtrace.resolve."""

from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import patch

import pytest

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.resolve import (
    ResolveResult,
    _extract_host,
    resolve_url,
    resolve_store,
)
from reqtrace.storage import LogStore


def _make_entry(url: str = "http://example.com/api") -> RequestLogEntry:
    return RequestLogEntry(
        id=str(uuid.uuid4()),
        timestamp=datetime.utcnow().isoformat(),
        request=HttpRequest(method="GET", url=url, headers={}, body=None),
        response=HttpResponse(status_code=200, headers={}, body=None),
    )


def _make_store(*urls: str) -> LogStore:
    store = LogStore()
    for url in urls:
        store.add(_make_entry(url))
    return store


class TestExtractHost:
    def test_http_url(self):
        assert _extract_host("http://example.com/path") == "example.com"

    def test_https_url_with_port(self):
        assert _extract_host("https://api.example.com:8443/v1") == "api.example.com"

    def test_empty_string_returns_none(self):
        assert _extract_host("") is None

    def test_no_scheme_returns_none(self):
        # urlparse without scheme puts everything in path
        result = _extract_host("not-a-url")
        assert result is None


class TestResolveResult:
    def test_ok_when_ips_present(self):
        r = ResolveResult(entry_id="1", url="http://x.com", host="x.com", resolved_ips=["1.2.3.4"])
        assert r.ok is True

    def test_not_ok_when_error(self):
        r = ResolveResult(entry_id="1", url="http://x.com", host="x.com", error="fail")
        assert r.ok is False

    def test_summary_ok(self):
        r = ResolveResult(entry_id="1", url="http://x.com", host="x.com", resolved_ips=["1.2.3.4"])
        assert "[OK]" in r.summary()
        assert "1.2.3.4" in r.summary()

    def test_summary_fail(self):
        r = ResolveResult(entry_id="1", url="http://x.com", host="x.com", error="NXDOMAIN")
        assert "[FAIL]" in r.summary()
        assert "NXDOMAIN" in r.summary()


class TestResolveUrl:
    def test_successful_resolution(self):
        with patch("reqtrace.resolve.socket.getaddrinfo") as mock_gai:
            mock_gai.return_value = [(None, None, None, None, ("93.184.216.34", 0))]
            result = resolve_url("abc", "http://example.com/path")
        assert result.ok
        assert "93.184.216.34" in result.resolved_ips
        assert result.host == "example.com"

    def test_dns_failure(self):
        import socket
        with patch("reqtrace.resolve.socket.getaddrinfo", side_effect=socket.gaierror("NXDOMAIN")):
            result = resolve_url("abc", "http://no-such-host.invalid/")
        assert not result.ok
        assert "NXDOMAIN" in result.error

    def test_bad_url_returns_error(self):
        result = resolve_url("abc", "")
        assert not result.ok
        assert result.error is not None


class TestResolveStore:
    def test_empty_store_returns_empty(self):
        store = LogStore()
        assert resolve_store(store) == []

    def test_resolves_all_entries(self):
        store = _make_store("http://a.com", "http://b.com")
        with patch("reqtrace.resolve.socket.getaddrinfo") as mock_gai:
            mock_gai.return_value = [(None, None, None, None, ("1.1.1.1", 0))]
            results = resolve_store(store)
        assert len(results) == 2

    def test_resolve_single_entry_by_id(self):
        store = _make_store("http://example.com")
        entry = store.all()[0]
        with patch("reqtrace.resolve.socket.getaddrinfo") as mock_gai:
            mock_gai.return_value = [(None, None, None, None, ("1.1.1.1", 0))]
            results = resolve_store(store, entry_id=entry.id)
        assert len(results) == 1
        assert results[0].entry_id == entry.id

    def test_missing_id_returns_empty(self):
        store = _make_store("http://example.com")
        results = resolve_store(store, entry_id="nonexistent-id")
        assert results == []
