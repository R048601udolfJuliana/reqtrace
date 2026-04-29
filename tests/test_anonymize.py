"""Tests for reqtrace.anonymize module."""

import pytest
from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.anonymize import anonymize_entry, REDACTED, DEFAULT_SENSITIVE_HEADERS


def _make_entry(
    headers=None,
    body=None,
    resp_headers=None,
    resp_body=None,
    include_response=True,
):
    req = HttpRequest(
        method="POST",
        url="http://example.com/api",
        headers=headers or {"Authorization": "Bearer secret", "Content-Type": "application/json"},
        body=body,
    )
    resp = None
    if include_response:
        resp = HttpResponse(
            status_code=200,
            headers=resp_headers or {"Set-Cookie": "session=abc", "Content-Type": "application/json"},
            body=resp_body,
            elapsed_ms=42,
        )
    return RequestLogEntry(request=req, response=resp)


class TestAnonymizeEntry:
    def test_authorization_header_redacted(self):
        entry = _make_entry()
        clean = anonymize_entry(entry)
        assert clean.request.headers["Authorization"] == REDACTED

    def test_non_sensitive_header_preserved(self):
        entry = _make_entry()
        clean = anonymize_entry(entry)
        assert clean.request.headers["Content-Type"] == "application/json"

    def test_response_set_cookie_redacted(self):
        entry = _make_entry()
        clean = anonymize_entry(entry)
        assert clean.response.headers["Set-Cookie"] == REDACTED

    def test_no_response_returns_none_response(self):
        entry = _make_entry(include_response=False)
        clean = anonymize_entry(entry)
        assert clean.response is None

    def test_body_pattern_redacted(self):
        entry = _make_entry(body='{"password": "hunter2", "user": "alice"}')
        clean = anonymize_entry(entry, body_patterns=[r'"password":\s*"[^"]*"'])
        assert "hunter2" not in clean.request.body
        assert REDACTED in clean.request.body
        assert "alice" in clean.request.body

    def test_response_body_pattern_redacted(self):
        entry = _make_entry(resp_body='{"token": "abc123"}')
        clean = anonymize_entry(entry, body_patterns=[r'"token":\s*"[^"]*"'])
        assert "abc123" not in clean.response.body

    def test_original_entry_not_mutated(self):
        entry = _make_entry()
        _ = anonymize_entry(entry)
        assert entry.request.headers["Authorization"] == "Bearer secret"

    def test_id_and_timestamp_preserved(self):
        entry = _make_entry()
        clean = anonymize_entry(entry)
        assert clean.id == entry.id
        assert clean.timestamp == entry.timestamp

    def test_extra_sensitive_header(self):
        headers = {"X-Custom-Secret": "topsecret", "Accept": "*/*"}
        entry = _make_entry(headers=headers)
        clean = anonymize_entry(entry, sensitive_headers={"x-custom-secret"})
        assert clean.request.headers["X-Custom-Secret"] == REDACTED
        assert clean.request.headers["Accept"] == "*/*"

    def test_none_body_stays_none(self):
        entry = _make_entry(body=None)
        clean = anonymize_entry(entry, body_patterns=[r"secret"])
        assert clean.request.body is None
