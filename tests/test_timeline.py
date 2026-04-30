"""Tests for reqtrace.timeline."""

from __future__ import annotations

import pytest

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.timeline import (
    bucket_by_minute,
    format_timeline,
    sort_entries,
)


def _make_entry(
    entry_id: str,
    timestamp: str,
    method: str = "GET",
    url: str = "http://example.com/api",
    status: int = 200,
) -> RequestLogEntry:
    req = HttpRequest(method=method, url=url, headers={}, body=None)
    resp = HttpResponse(status_code=status, headers={}, body=None)
    return RequestLogEntry(id=entry_id, timestamp=timestamp, request=req, response=resp)


class TestSortEntries:
    def test_sorts_ascending(self):
        e1 = _make_entry("a", "2024-01-01T10:00:00Z")
        e2 = _make_entry("b", "2024-01-01T09:00:00Z")
        result = sort_entries([e1, e2])
        assert [r.id for r in result] == ["b", "a"]

    def test_sorts_descending(self):
        e1 = _make_entry("a", "2024-01-01T10:00:00Z")
        e2 = _make_entry("b", "2024-01-01T09:00:00Z")
        result = sort_entries([e1, e2], descending=True)
        assert [r.id for r in result] == ["a", "b"]

    def test_empty_list(self):
        assert sort_entries([]) == []

    def test_single_entry_unchanged(self):
        e = _make_entry("only", "2024-01-01T10:00:00Z")
        assert sort_entries([e]) == [e]


class TestBucketByMinute:
    def test_same_minute_grouped(self):
        e1 = _make_entry("a", "2024-01-01T10:01:05Z")
        e2 = _make_entry("b", "2024-01-01T10:01:45Z")
        buckets = bucket_by_minute([e1, e2])
        assert "2024-01-01T10:01" in buckets
        assert len(buckets["2024-01-01T10:01"]) == 2

    def test_different_minutes_separate(self):
        e1 = _make_entry("a", "2024-01-01T10:01:00Z")
        e2 = _make_entry("b", "2024-01-01T10:02:00Z")
        buckets = bucket_by_minute([e1, e2])
        assert len(buckets) == 2

    def test_empty_returns_empty_dict(self):
        assert bucket_by_minute([]) == {}

    def test_bucket_key_format(self):
        """Bucket keys should be truncated to minute precision (no seconds)."""
        e = _make_entry("a", "2024-06-20T14:55:30Z")
        buckets = bucket_by_minute([e])
        keys = list(buckets.keys())
        assert len(keys) == 1
        assert keys[0] == "2024-06-20T14:55"


class TestFormatTimeline:
    def test_empty_entries(self):
        assert format_timeline([]) == "No entries."

    def test_contains_bucket_header(self):
        e = _make_entry("abc12345", "2024-03-15T08:30:00Z")
        output = format_timeline([e])
        assert "[2024-03-15T08:30]" in output

    def test_contains_entry_id_prefix(self):
        e = _make_entry("deadbeef-1234", "2024-03-15T08:30:00Z")
        output = format_timeline([e])
        assert "deadbeef" in output

    def test_contains_status_code(self):
        e = _make_entry("x", "2024-03-15T08:30:00Z", status=404)
        output = format_timeline([e])
        assert "404" in output

    def test_no_response_shows_dashes(self):
        req = HttpRequest(method="GET", url="http://example.com", headers={}, body=None)
        e = RequestLogEntry(id="noresp", timestamp="2024-03-15T08:30:00Z", request=req, response=None)
        output = format_timeline([e])
        assert "---" in output

    def test_descending_order(self):
        e1 = _make_entry("first", "2024-01-01T10:00:00Z")
        e2 = _make_entry("second", "2024-01-01T11:00:00Z")
        output = format_timeline([e1, e2], descending=True)
        assert output.index("second") < output.index("first")
