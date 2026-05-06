"""Tests for reqtrace.truncate."""

from __future__ import annotations

import pytest

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.truncate import (
    DEFAULT_MAX_BODY_BYTES,
    _TRUNCATION_MARKER,
    _truncate_body,
    is_truncated,
    truncate_entry,
    truncate_request,
    truncate_response,
)


def _make_entry(
    req_body: str | None = None,
    resp_body: str | None = None,
    with_response: bool = True,
) -> RequestLogEntry:
    req = HttpRequest(method="POST", url="http://example.com/api", headers={}, body=req_body)
    resp = (
        HttpResponse(status_code=200, headers={}, body=resp_body)
        if with_response
        else None
    )
    return RequestLogEntry(request=req, response=resp)


class TestTruncateBody:
    def test_none_returns_none(self):
        assert _truncate_body(None, 100) is None

    def test_short_body_unchanged(self):
        assert _truncate_body("hello", 100) == "hello"

    def test_exact_length_unchanged(self):
        text = "x" * 10
        assert _truncate_body(text, 10) == text

    def test_long_body_truncated(self):
        text = "a" * 600
        result = _truncate_body(text, DEFAULT_MAX_BODY_BYTES)
        assert len(result) == DEFAULT_MAX_BODY_BYTES + len(_TRUNCATION_MARKER)
        assert result.endswith(_TRUNCATION_MARKER)

    def test_custom_max_bytes(self):
        result = _truncate_body("abcdef", 3)
        assert result == "abc" + _TRUNCATION_MARKER


class TestIsTruncated:
    def test_truncated_text(self):
        assert is_truncated("some text" + _TRUNCATION_MARKER)

    def test_normal_text(self):
        assert not is_truncated("normal body")

    def test_none_is_false(self):
        assert not is_truncated(None)


class TestTruncateRequest:
    def test_short_body_unchanged(self):
        req = HttpRequest(method="GET", url="http://x.com", headers={}, body="short")
        result = truncate_request(req)
        assert result.body == "short"

    def test_long_body_truncated(self):
        req = HttpRequest(method="POST", url="http://x.com", headers={}, body="z" * 1000)
        result = truncate_request(req, max_bytes=50)
        assert is_truncated(result.body)
        assert result.method == "POST"
        assert result.url == "http://x.com"

    def test_original_not_modified(self):
        body = "y" * 1000
        req = HttpRequest(method="PUT", url="http://x.com", headers={}, body=body)
        truncate_request(req, max_bytes=10)
        assert req.body == body


class TestTruncateResponse:
    def test_short_body_unchanged(self):
        resp = HttpResponse(status_code=200, headers={}, body="ok")
        assert truncate_response(resp).body == "ok"

    def test_long_body_truncated(self):
        resp = HttpResponse(status_code=200, headers={}, body="r" * 1000)
        result = truncate_response(resp, max_bytes=100)
        assert is_truncated(result.body)
        assert result.status_code == 200


class TestTruncateEntry:
    def test_preserves_id_and_timestamp(self):
        entry = _make_entry(req_body="x" * 1000, resp_body="y" * 1000)
        result = truncate_entry(entry, max_bytes=50)
        assert result.id == entry.id
        assert result.timestamp == entry.timestamp

    def test_request_body_truncated(self):
        entry = _make_entry(req_body="a" * 1000)
        result = truncate_entry(entry, max_bytes=100)
        assert is_truncated(result.request.body)

    def test_response_body_truncated(self):
        entry = _make_entry(resp_body="b" * 1000)
        result = truncate_entry(entry, max_bytes=100)
        assert result.response is not None
        assert is_truncated(result.response.body)

    def test_no_response_handled(self):
        entry = _make_entry(with_response=False)
        result = truncate_entry(entry)
        assert result.response is None

    def test_original_entry_not_modified(self):
        body = "c" * 1000
        entry = _make_entry(req_body=body)
        truncate_entry(entry, max_bytes=50)
        assert entry.request.body == body
