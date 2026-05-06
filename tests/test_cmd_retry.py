"""Tests for reqtrace.cmd_retry."""

from __future__ import annotations

import argparse
from unittest.mock import patch

from reqtrace.cmd_retry import cmd_retry
from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.retry import RetryResult
from reqtrace.storage import LogStore


def _make_entry(entry_id: str = "abc123") -> RequestLogEntry:
    req = HttpRequest(method="GET", url="http://example.com/", headers={}, body=None)
    e = RequestLogEntry(request=req)
    e.id = entry_id
    return e


def _make_store(entry: RequestLogEntry | None = None) -> LogStore:
    store = LogStore()
    if entry:
        store.add(entry)
    return store


def _args(**kwargs) -> argparse.Namespace:
    defaults = dict(
        id="abc123",
        max_attempts=3,
        backoff=1.0,
        retry_on=[500, 502, 503, 504],
        host=None,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdRetry:
    def test_prints_not_found_for_missing_id(self, capsys):
        store = _make_store()
        cmd_retry(_args(id="nope"), store)
        out = capsys.readouterr().out
        assert "not found" in out

    def test_prints_success_on_200(self, capsys):
        entry = _make_entry()
        store = _make_store(entry)
        result = RetryResult(attempts=1, final_status=200, success=True)
        with patch("reqtrace.cmd_retry.retry_entry", return_value=result):
            cmd_retry(_args(id=entry.id), store)
        out = capsys.readouterr().out
        assert "SUCCESS" in out
        assert "200" in out

    def test_prints_failed_on_exhaustion(self, capsys):
        entry = _make_entry()
        store = _make_store(entry)
        result = RetryResult(attempts=3, final_status=503, success=False)
        with patch("reqtrace.cmd_retry.retry_entry", return_value=result):
            cmd_retry(_args(id=entry.id), store)
        out = capsys.readouterr().out
        assert "FAILED" in out
        assert "503" in out

    def test_prints_error_message_on_connection_failure(self, capsys):
        entry = _make_entry()
        store = _make_store(entry)
        result = RetryResult(attempts=2, final_status=None, success=False, error="conn refused")
        with patch("reqtrace.cmd_retry.retry_entry", return_value=result):
            cmd_retry(_args(id=entry.id), store)
        out = capsys.readouterr().out
        assert "conn refused" in out

    def test_policy_built_from_args(self, capsys):
        entry = _make_entry()
        store = _make_store(entry)
        result = RetryResult(attempts=1, final_status=200, success=True)
        with patch("reqtrace.cmd_retry.retry_entry", return_value=result) as mock_retry:
            cmd_retry(_args(id=entry.id, max_attempts=5, backoff=0.5, retry_on=[500], host="h:9"), store)
        policy = mock_retry.call_args[0][1]
        assert policy.max_attempts == 5
        assert policy.backoff_base == 0.5
        assert policy.retry_on_status == [500]
        assert policy.override_host == "h:9"
