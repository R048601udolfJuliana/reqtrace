"""Tests for reqtrace.badge."""

from __future__ import annotations

import pytest

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.badge import (
    format_badge_line,
    method_badge,
    status_badge,
    tag_badge,
)


def _make_entry(
    method: str = "GET",
    url: str = "http://example.com/api",
    status: int | None = 200,
    tags: list[str] | None = None,
) -> RequestLogEntry:
    request = HttpRequest(method=method, url=url, headers={}, body=None)
    response = (
        HttpResponse(status_code=status, headers={}, body=None)
        if status is not None
        else None
    )
    metadata: dict = {}
    if tags:
        metadata["tags"] = tags
    return RequestLogEntry(
        request=request,
        response=response,
        metadata=metadata,
    )


class TestStatusBadge:
    def test_2xx_contains_code(self):
        entry = _make_entry(status=200)
        badge = status_badge(entry, use_colour=False)
        assert "200" in badge

    def test_4xx_contains_code(self):
        entry = _make_entry(status=404)
        badge = status_badge(entry, use_colour=False)
        assert "404" in badge

    def test_5xx_contains_code(self):
        entry = _make_entry(status=500)
        badge = status_badge(entry, use_colour=False)
        assert "500" in badge

    def test_no_response_shows_no_response(self):
        entry = _make_entry(status=None)
        badge = status_badge(entry, use_colour=False)
        assert "NO RESPONSE" in badge

    def test_colour_enabled_includes_ansi(self):
        entry = _make_entry(status=200)
        badge = status_badge(entry, use_colour=True)
        assert "\033[" in badge


class TestMethodBadge:
    def test_get_contains_get(self):
        entry = _make_entry(method="GET")
        badge = method_badge(entry, use_colour=False)
        assert "GET" in badge

    def test_delete_contains_delete(self):
        entry = _make_entry(method="DELETE")
        badge = method_badge(entry, use_colour=False)
        assert "DELETE" in badge

    def test_unknown_method_still_shown(self):
        entry = _make_entry(method="OPTIONS")
        badge = method_badge(entry, use_colour=False)
        assert "OPTIONS" in badge


class TestTagBadge:
    def test_no_tags_returns_empty_string(self):
        entry = _make_entry(tags=None)
        assert tag_badge(entry, use_colour=False) == ""

    def test_single_tag_shown(self):
        entry = _make_entry(tags=["important"])
        badge = tag_badge(entry, use_colour=False)
        assert "important" in badge

    def test_multiple_tags_sorted(self):
        entry = _make_entry(tags=["zebra", "alpha"])
        badge = tag_badge(entry, use_colour=False)
        assert badge.index("alpha") < badge.index("zebra")


class TestFormatBadgeLine:
    def test_contains_url(self):
        entry = _make_entry(url="http://api.test/v1/users")
        line = format_badge_line(entry, use_colour=False)
        assert "http://api.test/v1/users" in line

    def test_contains_method_and_status(self):
        entry = _make_entry(method="POST", status=201)
        line = format_badge_line(entry, use_colour=False)
        assert "POST" in line
        assert "201" in line

    def test_tag_section_absent_when_no_tags(self):
        entry = _make_entry(tags=None)
        line = format_badge_line(entry, use_colour=False)
        assert "tags" not in line

    def test_tag_section_present_when_tagged(self):
        entry = _make_entry(tags=["review"])
        line = format_badge_line(entry, use_colour=False)
        assert "review" in line
