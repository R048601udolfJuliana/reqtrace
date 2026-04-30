"""Tests for reqtrace.highlight."""

import pytest
from reqtrace.highlight import (
    method_colour,
    status_colour,
    url_highlight,
    header_highlight,
    bold,
)


# ---------------------------------------------------------------------------
# method_colour
# ---------------------------------------------------------------------------

class TestMethodColour:
    def test_get_contains_green(self):
        result = method_colour("GET", enabled=True)
        assert "\033[32m" in result
        assert "GET" in result

    def test_delete_contains_red(self):
        result = method_colour("DELETE", enabled=True)
        assert "\033[31m" in result

    def test_post_contains_cyan(self):
        result = method_colour("POST", enabled=True)
        assert "\033[36m" in result

    def test_disabled_returns_plain_text(self):
        result = method_colour("GET", enabled=False)
        assert result == "GET"
        assert "\033[" not in result

    def test_lowercase_input_normalised(self):
        result = method_colour("get", enabled=True)
        assert "GET" in result


# ---------------------------------------------------------------------------
# status_colour
# ---------------------------------------------------------------------------

class TestStatusColour:
    def test_2xx_green(self):
        assert "\033[32m" in status_colour(200)

    def test_3xx_cyan(self):
        assert "\033[36m" in status_colour(301)

    def test_4xx_yellow(self):
        assert "\033[33m" in status_colour(404)

    def test_5xx_red(self):
        assert "\033[31m" in status_colour(500)

    def test_none_returns_na(self):
        result = status_colour(None, enabled=True)
        assert "N/A" in result

    def test_disabled_returns_plain_number(self):
        result = status_colour(200, enabled=False)
        assert result == "200"
        assert "\033[" not in result


# ---------------------------------------------------------------------------
# url_highlight
# ---------------------------------------------------------------------------

class TestUrlHighlight:
    def test_bold_applied_to_host(self):
        result = url_highlight("http://example.com/path", enabled=True)
        assert "\033[1m" in result
        assert "/path" in result

    def test_disabled_returns_original(self):
        url = "http://example.com/path"
        assert url_highlight(url, enabled=False) == url

    def test_no_scheme_returned_as_is(self):
        url = "example.com/path"
        result = url_highlight(url, enabled=True)
        assert url in result

    def test_url_without_path(self):
        result = url_highlight("https://api.local", enabled=True)
        assert "api.local" in result


# ---------------------------------------------------------------------------
# header_highlight / bold
# ---------------------------------------------------------------------------

class TestMisc:
    def test_header_highlight_contains_name_and_value(self):
        result = header_highlight("Content-Type", "application/json")
        assert "Content-Type" in result
        assert "application/json" in result

    def test_header_highlight_disabled(self):
        result = header_highlight("X-Foo", "bar", enabled=False)
        assert result == "X-Foo: bar"

    def test_bold_enabled(self):
        assert "\033[1m" in bold("hello", enabled=True)

    def test_bold_disabled(self):
        assert bold("hello", enabled=False) == "hello"
