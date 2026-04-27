"""Tests for reqtrace.search."""
from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.search import search_store, search_by_body


def _make_entry(
    method: str = "GET",
    host: str = "api.local",
    path: str = "/items",
    status_code: int | None = 200,
    body: str | None = None,
) -> RequestLogEntry:
    req = HttpRequest(method=method, host=host, path=path, headers={}, body=body)
    resp = HttpResponse(status_code=status_code, headers={}, body=None) if status_code else None
    return RequestLogEntry(
        id=str(uuid.uuid4()),
        timestamp=datetime.utcnow().isoformat(),
        request=req,
        response=resp,
    )


def _store(*entries: RequestLogEntry) -> LogStore:
    s = LogStore()
    for e in entries:
        s.add(e)
    return s


class TestSearchStore:
    def test_empty_store_returns_empty(self):
        assert search_store(LogStore()) == []

    def test_no_criteria_returns_all(self):
        s = _store(_make_entry(), _make_entry(), _make_entry())
        assert len(search_store(s)) == 3

    def test_filter_by_method(self):
        s = _store(_make_entry(method="GET"), _make_entry(method="POST"))
        result = search_store(s, method="POST")
        assert len(result) == 1
        assert result[0].request.method == "POST"

    def test_filter_by_host(self):
        s = _store(_make_entry(host="a.local"), _make_entry(host="b.local"))
        result = search_store(s, host="a.local")
        assert len(result) == 1

    def test_filter_by_path_prefix(self):
        s = _store(
            _make_entry(path="/api/users"),
            _make_entry(path="/api/items"),
            _make_entry(path="/health"),
        )
        result = search_store(s, path_prefix="/api")
        assert len(result) == 2

    def test_filter_by_status_code(self):
        s = _store(
            _make_entry(status_code=200),
            _make_entry(status_code=404),
            _make_entry(status_code=200),
        )
        result = search_store(s, status_code=404)
        assert len(result) == 1

    def test_filter_body_contains(self):
        s = _store(
            _make_entry(body='{"name": "alice"}'),
            _make_entry(body='{"name": "bob"}'),
            _make_entry(body=None),
        )
        result = search_store(s, body_contains="alice")
        assert len(result) == 1

    def test_limit_applied(self):
        s = _store(*[_make_entry() for _ in range(10)])
        result = search_store(s, limit=3)
        assert len(result) == 3

    def test_combined_method_and_status(self):
        s = _store(
            _make_entry(method="GET", status_code=200),
            _make_entry(method="GET", status_code=500),
            _make_entry(method="POST", status_code=200),
        )
        result = search_store(s, method="GET", status_code=200)
        assert len(result) == 1


class TestSearchByBody:
    def test_finds_matching_entries(self):
        s = _store(
            _make_entry(body="hello world"),
            _make_entry(body="goodbye world"),
            _make_entry(body="nothing here"),
        )
        result = search_by_body(s, "world")
        assert len(result) == 2

    def test_no_match_returns_empty(self):
        s = _store(_make_entry(body="hello"))
        assert search_by_body(s, "xyz") == []

    def test_limit_respected(self):
        s = _store(*[_make_entry(body="token") for _ in range(5)])
        result = search_by_body(s, "token", limit=2)
        assert len(result) == 2
