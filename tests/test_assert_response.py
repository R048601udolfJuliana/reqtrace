"""Tests for reqtrace.assert_response."""

import pytest
from reqtrace.assert_response import AssertionFailure, AssertionResult, assert_entry
from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry


def _make_entry(
    status: int = 200,
    body: str = '{"ok": true}',
    headers: dict = None,
    latency_ms: float = None,
) -> RequestLogEntry:
    req = HttpRequest(method="GET", url="http://example.com/api", headers={}, body=None)
    resp = HttpResponse(
        status_code=status,
        headers=headers or {"Content-Type": "application/json"},
        body=body,
    )
    meta = {}
    if latency_ms is not None:
        meta["latency_ms"] = latency_ms
    return RequestLogEntry(
        request=req,
        response=resp,
        timestamp="2024-01-01T00:00:00",
        metadata=meta,
    )


class TestAssertionResult:
    def test_passed_when_no_failures(self):
        r = AssertionResult(entry_id="abc")
        assert r.passed is True

    def test_failed_when_has_failures(self):
        r = AssertionResult(entry_id="abc", failures=[AssertionFailure("x", 1, 2)])
        assert r.passed is False

    def test_summary_pass(self):
        r = AssertionResult(entry_id="abc")
        assert "PASS" in r.summary()

    def test_summary_fail_contains_count(self):
        r = AssertionResult(
            entry_id="abc",
            failures=[AssertionFailure("status_code", 200, 404)],
        )
        assert "FAIL" in r.summary()
        assert "1 failure" in r.summary()


class TestAssertEntry:
    def test_status_pass(self):
        entry = _make_entry(status=200)
        result = assert_entry(entry, status=200)
        assert result.passed

    def test_status_fail(self):
        entry = _make_entry(status=404)
        result = assert_entry(entry, status=200)
        assert not result.passed
        assert result.failures[0].field == "status_code"

    def test_body_contains_pass(self):
        entry = _make_entry(body="hello world")
        result = assert_entry(entry, body_contains="hello")
        assert result.passed

    def test_body_contains_fail(self):
        entry = _make_entry(body="goodbye")
        result = assert_entry(entry, body_contains="hello")
        assert not result.passed

    def test_header_pass(self):
        entry = _make_entry(headers={"X-Token": "abc"})
        result = assert_entry(entry, headers_contain={"X-Token": "abc"})
        assert result.passed

    def test_header_fail(self):
        entry = _make_entry(headers={"X-Token": "abc"})
        result = assert_entry(entry, headers_contain={"X-Token": "wrong"})
        assert not result.passed
        assert "header[X-Token]" in result.failures[0].field

    def test_latency_pass(self):
        entry = _make_entry(latency_ms=50.0)
        result = assert_entry(entry, max_latency_ms=100.0)
        assert result.passed

    def test_latency_fail(self):
        entry = _make_entry(latency_ms=200.0)
        result = assert_entry(entry, max_latency_ms=100.0)
        assert not result.passed
        assert result.failures[0].field == "latency_ms"

    def test_no_response_status_fails(self):
        req = HttpRequest(method="GET", url="http://x.com", headers={}, body=None)
        entry = RequestLogEntry(request=req, response=None, timestamp="2024-01-01T00:00:00")
        result = assert_entry(entry, status=200)
        assert not result.passed

    def test_multiple_failures_collected(self):
        entry = _make_entry(status=500, body="error")
        result = assert_entry(entry, status=200, body_contains="ok")
        assert len(result.failures) == 2
