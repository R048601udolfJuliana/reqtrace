"""Tests for reqtrace.compare."""

from __future__ import annotations

import pytest

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.compare import compare_entries, CompareResult, _str_similarity, _header_similarity


def _make_entry(
    method: str = "GET",
    url: str = "http://example.com/api",
    headers: dict | None = None,
    body: str | None = None,
    entry_id: str = "abc",
) -> RequestLogEntry:
    req = HttpRequest(method=method, url=url, headers=headers or {}, body=body)
    return RequestLogEntry(id=entry_id, timestamp="2024-01-01T00:00:00", request=req)


class TestStrSimilarity:
    def test_identical_strings(self):
        assert _str_similarity("hello", "hello") == 1.0

    def test_completely_different(self):
        score = _str_similarity("abc", "xyz")
        assert score == 0.0

    def test_partial_overlap(self):
        score = _str_similarity("abc", "abc123")
        assert 0.0 < score < 1.0

    def test_empty_strings(self):
        assert _str_similarity("", "") == 1.0


class TestHeaderSimilarity:
    def test_identical_headers(self):
        h = {"Content-Type": "application/json"}
        assert _header_similarity(h, h) == 1.0

    def test_no_headers(self):
        assert _header_similarity({}, {}) == 1.0

    def test_partial_match(self):
        ha = {"Content-Type": "application/json", "X-Custom": "foo"}
        hb = {"Content-Type": "application/json", "X-Custom": "bar"}
        score = _header_similarity(ha, hb)
        assert 0.0 < score < 1.0


class TestCompareEntries:
    def test_identical_entries_score_one(self):
        a = _make_entry(entry_id="a")
        b = _make_entry(entry_id="b")
        result = compare_entries(a, b)
        assert result.score == 1.0

    def test_different_method_lowers_score(self):
        a = _make_entry(method="GET", entry_id="a")
        b = _make_entry(method="POST", entry_id="b")
        result = compare_entries(a, b)
        assert result.score < 1.0
        assert result.field_scores["method"] == 0.0

    def test_different_url_lowers_score(self):
        a = _make_entry(url="http://example.com/foo", entry_id="a")
        b = _make_entry(url="http://other.org/bar", entry_id="b")
        result = compare_entries(a, b)
        assert result.score < 1.0

    def test_returns_compare_result_instance(self):
        a = _make_entry(entry_id="a")
        b = _make_entry(entry_id="b")
        result = compare_entries(a, b)
        assert isinstance(result, CompareResult)

    def test_field_scores_keys_present(self):
        a = _make_entry(entry_id="a")
        b = _make_entry(entry_id="b")
        result = compare_entries(a, b)
        assert set(result.field_scores.keys()) == {"method", "url", "headers", "body"}

    def test_custom_weights(self):
        a = _make_entry(method="GET", entry_id="a")
        b = _make_entry(method="POST", entry_id="b")
        result = compare_entries(a, b, weights={"method": 1.0, "url": 0.0, "headers": 0.0, "body": 0.0})
        assert result.score == 0.0

    def test_summary_contains_percentage(self):
        a = _make_entry(entry_id="a")
        b = _make_entry(entry_id="b")
        result = compare_entries(a, b)
        assert "100%" in result.summary
