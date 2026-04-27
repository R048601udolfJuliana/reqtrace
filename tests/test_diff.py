"""Tests for reqtrace.diff module."""

import pytest
from reqtrace.diff import diff_entries, EntryDiff, FieldDiff
from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry


def _make_entry(
    entry_id: str = "abc",
    method: str = "GET",
    url: str = "http://example.com/api",
    headers: dict = None,
    body: str = None,
    status_code: int = 200,
    resp_body: str = "{}",
) -> RequestLogEntry:
    req = HttpRequest(
        method=method,
        url=url,
        headers=headers or {"Content-Type": "application/json"},
        body=body,
    )
    resp = HttpResponse(
        status_code=status_code,
        headers={"Content-Type": "application/json"},
        body=resp_body,
    )
    return RequestLogEntry(id=entry_id, request=req, response=resp)


class TestDiffEntries:
    def test_identical_entries_no_diff(self):
        a = _make_entry("id1")
        b = _make_entry("id2")
        result = diff_entries(a, b)
        assert isinstance(result, EntryDiff)
        assert not result.has_differences

    def test_different_method(self):
        a = _make_entry("id1", method="GET")
        b = _make_entry("id2", method="POST")
        result = diff_entries(a, b)
        assert result.has_differences
        fields = [d.field for d in result.diffs]
        assert "method" in fields

    def test_different_url(self):
        a = _make_entry("id1", url="http://example.com/a")
        b = _make_entry("id2", url="http://example.com/b")
        result = diff_entries(a, b)
        assert result.has_differences
        assert any(d.field == "url" for d in result.diffs)

    def test_different_status_code(self):
        a = _make_entry("id1", status_code=200)
        b = _make_entry("id2", status_code=404)
        result = diff_entries(a, b)
        assert any(d.field == "response.status_code" for d in result.diffs)

    def test_different_body(self):
        a = _make_entry("id1", resp_body='{"x": 1}')
        b = _make_entry("id2", resp_body='{"x": 2}')
        result = diff_entries(a, b)
        assert any(d.field == "response.body" for d in result.diffs)

    def test_one_response_none(self):
        a = _make_entry("id1")
        b = _make_entry("id2")
        b.response = None
        result = diff_entries(a, b)
        assert result.has_differences
        assert any(d.field == "response" for d in result.diffs)

    def test_both_responses_none(self):
        a = _make_entry("id1")
        b = _make_entry("id2")
        a.response = None
        b.response = None
        result = diff_entries(a, b)
        assert not result.has_differences

    def test_summary_no_diff(self):
        a = _make_entry("id1")
        b = _make_entry("id2")
        result = diff_entries(a, b)
        assert "No differences" in result.summary()

    def test_summary_with_diff(self):
        a = _make_entry("id1", method="GET")
        b = _make_entry("id2", method="DELETE")
        result = diff_entries(a, b)
        summary = result.summary()
        assert "method" in summary
        assert "GET" in summary
        assert "DELETE" in summary

    def test_ids_stored_on_result(self):
        a = _make_entry("left-id")
        b = _make_entry("right-id")
        result = diff_entries(a, b)
        assert result.left_id == "left-id"
        assert result.right_id == "right-id"
