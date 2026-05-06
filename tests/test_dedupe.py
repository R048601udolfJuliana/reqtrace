"""Tests for reqtrace.dedupe."""

from __future__ import annotations

import pytest

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.dedupe import (
    _entry_fingerprint,
    find_duplicates,
    deduplicate,
    dedupe_store,
)


def _make_entry(
    id: str,
    method: str = "GET",
    url: str = "http://example.com/api",
    body: str = "",
    status: int = 200,
) -> RequestLogEntry:
    req = HttpRequest(method=method, url=url, headers={}, body=body)
    resp = HttpResponse(status_code=status, headers={}, body="ok")
    return RequestLogEntry(id=id, request=req, response=resp, timestamp="2024-01-01T00:00:00")


def _make_store(*entries: RequestLogEntry) -> LogStore:
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


class TestFingerprint:
    def test_same_method_url_body_equal(self):
        a = _make_entry("1", method="POST", url="http://x.com/", body="data")
        b = _make_entry("2", method="POST", url="http://x.com/", body="data")
        assert _entry_fingerprint(a) == _entry_fingerprint(b)

    def test_different_method_not_equal(self):
        a = _make_entry("1", method="GET")
        b = _make_entry("2", method="POST")
        assert _entry_fingerprint(a) != _entry_fingerprint(b)

    def test_trailing_slash_ignored_in_url(self):
        a = _make_entry("1", url="http://x.com/path")
        b = _make_entry("2", url="http://x.com/path/")
        assert _entry_fingerprint(a) == _entry_fingerprint(b)


class TestFindDuplicates:
    def test_no_duplicates_returns_empty(self):
        entries = [_make_entry("1", url="http://a.com"), _make_entry("2", url="http://b.com")]
        assert find_duplicates(entries) == {}

    def test_finds_duplicate_group(self):
        a = _make_entry("1", method="GET", url="http://x.com/api")
        b = _make_entry("2", method="GET", url="http://x.com/api")
        c = _make_entry("3", method="POST", url="http://x.com/api")
        result = find_duplicates([a, b, c])
        assert len(result) == 1
        group = next(iter(result.values()))
        assert {e.id for e in group} == {"1", "2"}

    def test_empty_list_returns_empty(self):
        assert find_duplicates([]) == {}


class TestDeduplicate:
    def test_keep_first_retains_earliest(self):
        a = _make_entry("1", url="http://x.com/api")
        b = _make_entry("2", url="http://x.com/api")
        result = deduplicate([a, b], keep="first")
        assert len(result) == 1
        assert result[0].id == "1"

    def test_keep_last_retains_latest(self):
        a = _make_entry("1", url="http://x.com/api")
        b = _make_entry("2", url="http://x.com/api")
        result = deduplicate([a, b], keep="last")
        assert len(result) == 1
        assert result[0].id == "2"

    def test_unique_entries_unchanged(self):
        a = _make_entry("1", url="http://a.com")
        b = _make_entry("2", url="http://b.com")
        result = deduplicate([a, b])
        assert len(result) == 2

    def test_invalid_keep_raises(self):
        with pytest.raises(ValueError):
            deduplicate([], keep="middle")

    def test_preserves_order(self):
        a = _make_entry("1", url="http://a.com")
        b = _make_entry("2", url="http://b.com")
        c = _make_entry("3", url="http://a.com")
        result = deduplicate([a, b, c], keep="first")
        assert [e.id for e in result] == ["1", "2"]


class TestDedupeStore:
    def test_removes_duplicates_and_returns_count(self):
        a = _make_entry("1", url="http://x.com/api")
        b = _make_entry("2", url="http://x.com/api")
        c = _make_entry("3", url="http://other.com")
        store = _make_store(a, b, c)
        removed = dedupe_store(store, keep="first")
        assert removed == 1
        assert len(store.all()) == 2

    def test_no_duplicates_removes_none(self):
        a = _make_entry("1", url="http://a.com")
        b = _make_entry("2", url="http://b.com")
        store = _make_store(a, b)
        assert dedupe_store(store) == 0
        assert len(store.all()) == 2
