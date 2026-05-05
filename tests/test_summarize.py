"""Tests for reqtrace.summarize."""

from __future__ import annotations

import pytest

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.summarize import _body_snippet, _status_class, format_summary, summarize_entry


def _make_entry(
    method: str = "GET",
    url: str = "http://example.com/api",
    req_body: str | None = None,
    status: int | None = 200,
    resp_body: str | None = '{"ok": true}',
    tags: list[str] | None = None,
) -> RequestLogEntry:
    req = HttpRequest(method=method, url=url, headers={}, body=req_body)
    resp = (
        HttpResponse(status_code=status, headers={}, body=resp_body)
        if status is not None
        else None
    )
    entry = RequestLogEntry(request=req, response=resp)
    if tags:
        entry.tags = set(tags)
    return entry


# ---------------------------------------------------------------------------
# _status_class
# ---------------------------------------------------------------------------

class TestStatusClass:
    def test_200_is_success(self):
        assert _status_class(200) == "2xx Success"

    def test_404_is_client_error(self):
        assert _status_class(404) == "4xx Client Error"

    def test_500_is_server_error(self):
        assert _status_class(500) == "5xx Server Error"

    def test_301_is_redirection(self):
        assert _status_class(301) == "3xx Redirection"

    def test_unknown_code(self):
        assert _status_class(999) == "Unknown"


# ---------------------------------------------------------------------------
# _body_snippet
# ---------------------------------------------------------------------------

class TestBodySnippet:
    def test_none_returns_empty_label(self):
        assert _body_snippet(None) == "(empty)"

    def test_short_body_unchanged(self):
        assert _body_snippet("hello") == "hello"

    def test_long_body_truncated(self):
        long = "x" * 100
        result = _body_snippet(long, max_len=10)
        assert result.endswith("…")
        assert len(result) == 12  # 10 chars + ellipsis (3 bytes but 1 char)


# ---------------------------------------------------------------------------
# summarize_entry
# ---------------------------------------------------------------------------

class TestSummarizeEntry:
    def test_contains_expected_keys(self):
        entry = _make_entry()
        s = summarize_entry(entry)
        for key in ("id", "timestamp", "method", "url", "status_code", "status_class", "tags"):
            assert key in s

    def test_method_and_url(self):
        entry = _make_entry(method="POST", url="http://api.local/v1/items")
        s = summarize_entry(entry)
        assert s["method"] == "POST"
        assert s["url"] == "http://api.local/v1/items"

    def test_no_response_sets_none(self):
        entry = _make_entry(status=None)
        s = summarize_entry(entry)
        assert s["status_code"] is None
        assert s["status_class"] == "No Response"

    def test_tags_included(self):
        entry = _make_entry(tags=["important", "auth"])
        s = summarize_entry(entry)
        assert set(s["tags"]) == {"important", "auth"}


# ---------------------------------------------------------------------------
# format_summary
# ---------------------------------------------------------------------------

class TestFormatSummary:
    def test_contains_method_and_url(self):
        entry = _make_entry(method="DELETE", url="http://example.com/item/1")
        line = format_summary(entry)
        assert "DELETE" in line
        assert "http://example.com/item/1" in line

    def test_contains_status_code(self):
        entry = _make_entry(status=404)
        line = format_summary(entry)
        assert "404" in line

    def test_no_response_label(self):
        entry = _make_entry(status=None)
        line = format_summary(entry)
        assert "No Response" in line

    def test_tags_shown_in_brackets(self):
        entry = _make_entry(tags=["debug"])
        line = format_summary(entry)
        assert "debug" in line
        assert "[" in line

    def test_no_tags_no_bracket(self):
        entry = _make_entry(tags=None)
        line = format_summary(entry)
        assert "[" not in line or line.index("[") == 1  # only the id bracket
