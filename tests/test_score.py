"""Tests for reqtrace.score."""

import pytest

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.score import ScoredEntry, score_entry, rank_entries


def _make_entry(
    method="GET",
    url="http://example.com/api",
    status=200,
    body="",
    metadata=None,
) -> RequestLogEntry:
    req = HttpRequest(method=method, url=url, headers={}, body=None)
    resp = HttpResponse(status_code=status, headers={}, body=body)
    return RequestLogEntry(
        request=req,
        response=resp,
        metadata=metadata or {},
    )


class TestScoreEntry:
    def test_ok_get_has_zero_base_score(self):
        entry = _make_entry(status=200)
        result = score_entry(entry)
        assert result.score == 0
        assert result.reasons == []

    def test_error_status_adds_points(self):
        entry = _make_entry(status=500)
        result = score_entry(entry)
        assert result.score >= 40
        assert any("status=500" in r for r in result.reasons)

    def test_404_also_flagged(self):
        entry = _make_entry(status=404)
        result = score_entry(entry)
        assert result.score >= 40

    def test_slow_response_adds_points(self):
        entry = _make_entry(metadata={"elapsed_ms": 2000})
        result = score_entry(entry)
        assert result.score >= 20
        assert any("slow" in r for r in result.reasons)

    def test_fast_response_not_flagged(self):
        entry = _make_entry(metadata={"elapsed_ms": 100})
        result = score_entry(entry)
        assert not any("slow" in r for r in result.reasons)

    def test_large_body_adds_points(self):
        big_body = "x" * 15_000
        entry = _make_entry(body=big_body)
        result = score_entry(entry)
        assert result.score >= 10
        assert any("large" in r for r in result.reasons)

    def test_delete_method_adds_points(self):
        entry = _make_entry(method="DELETE")
        result = score_entry(entry)
        assert result.score >= 5
        assert any("method=DELETE" in r for r in result.reasons)

    def test_get_method_not_flagged(self):
        entry = _make_entry(method="GET")
        result = score_entry(entry)
        assert not any("method=" in r for r in result.reasons)

    def test_pinned_tag_adds_points(self):
        entry = _make_entry(metadata={"tags": ["pinned"]})
        result = score_entry(entry)
        assert result.score >= 25
        assert "pinned" in result.reasons

    def test_bookmarked_tag_adds_points(self):
        entry = _make_entry(metadata={"tags": ["bookmark"]})
        result = score_entry(entry)
        assert result.score >= 10
        assert "bookmarked" in result.reasons

    def test_notes_add_points(self):
        entry = _make_entry(metadata={"notes": ["check this"]})
        result = score_entry(entry)
        assert result.score >= 15
        assert "has-notes" in result.reasons

    def test_summary_contains_score_and_method(self):
        entry = _make_entry(method="POST", status=503)
        result = score_entry(entry)
        s = result.summary()
        assert "score=" in s
        assert "POST" in s


class TestRankEntries:
    def test_empty_list_returns_empty(self):
        assert rank_entries([]) == []

    def test_higher_score_comes_first(self):
        low = _make_entry(status=200)
        high = _make_entry(status=500)
        ranked = rank_entries([low, high])
        assert ranked[0].entry is high

    def test_top_limits_results(self):
        entries = [_make_entry(status=200) for _ in range(10)]
        ranked = rank_entries(entries, top=3)
        assert len(ranked) == 3

    def test_top_zero_returns_all(self):
        entries = [_make_entry() for _ in range(5)]
        ranked = rank_entries(entries, top=0)
        assert len(ranked) == 5
