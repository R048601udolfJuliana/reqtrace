"""Tests for reqtrace.ratelimit."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
from typing import Optional
from unittest.mock import MagicMock

import pytest

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.ratelimit import (
    HostRateInfo,
    analyze_rate_limits,
    format_rate_report,
)
from reqtrace.cmd_ratelimit import cmd_ratelimit


def _make_entry(
    url: str = "http://api.example.com/v1/items",
    method: str = "GET",
    ts: Optional[str] = None,
    status: int = 200,
) -> RequestLogEntry:
    req = HttpRequest(method=method, url=url, headers={}, body=None)
    resp = HttpResponse(status_code=status, headers={}, body=None)
    return RequestLogEntry(
        request=req,
        response=resp,
        timestamp=ts or datetime.now(timezone.utc).isoformat(),
    )


def _ts(offset_seconds: float) -> str:
    base = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    return (base + timedelta(seconds=offset_seconds)).isoformat()


class TestAnalyzeRateLimits:
    def test_empty_returns_empty(self):
        assert analyze_rate_limits([]) == {}

    def test_single_entry_not_flagged_by_default(self):
        entry = _make_entry(ts=_ts(0))
        result = analyze_rate_limits([entry])
        assert len(result) == 1
        info = list(result.values())[0]
        assert not info.flagged

    def test_groups_by_host(self):
        e1 = _make_entry(url="http://alpha.io/a", ts=_ts(0))
        e2 = _make_entry(url="http://beta.io/b", ts=_ts(1))
        result = analyze_rate_limits([e1, e2])
        assert "alpha.io" in result
        assert "beta.io" in result

    def test_flags_when_rps_exceeds_threshold(self):
        # 20 requests in 1 second => 20 rps > default 10
        entries = [_make_entry(ts=_ts(i * 0.05)) for i in range(20)]
        result = analyze_rate_limits(entries, threshold_rps=10.0)
        info = list(result.values())[0]
        assert info.flagged
        assert info.total_requests == 20

    def test_does_not_flag_below_threshold(self):
        # 5 requests spread over 10 seconds => 0.5 rps
        entries = [_make_entry(ts=_ts(i * 2)) for i in range(5)]
        result = analyze_rate_limits(entries, threshold_rps=10.0)
        info = list(result.values())[0]
        assert not info.flagged

    def test_peak_requests_in_window(self):
        # 3 requests close together, then 1 far away
        entries = [
            _make_entry(ts=_ts(0)),
            _make_entry(ts=_ts(1)),
            _make_entry(ts=_ts(2)),
            _make_entry(ts=_ts(120)),
        ]
        result = analyze_rate_limits(entries, window_seconds=10.0)
        info = list(result.values())[0]
        assert info.peak_requests_in_window == 3


class TestFormatRateReport:
    def test_empty_returns_message(self):
        assert "No entries" in format_rate_report({})

    def test_contains_host(self):
        info = HostRateInfo(
            host="api.example.com",
            total_requests=5,
            window_seconds=10.0,
            requests_per_second=0.5,
            peak_requests_in_window=2,
            flagged=False,
        )
        report = format_rate_report({"api.example.com": info})
        assert "api.example.com" in report

    def test_flagged_label_present(self):
        info = HostRateInfo(
            host="fast.io",
            total_requests=100,
            window_seconds=5.0,
            requests_per_second=20.0,
            peak_requests_in_window=100,
            flagged=True,
        )
        report = format_rate_report({"fast.io": info})
        assert "FLAGGED" in report


class TestCmdRatelimit:
    def _args(self, threshold=10.0, window=60.0, flagged_only=False):
        ns = argparse.Namespace()
        ns.threshold = threshold
        ns.window = window
        ns.flagged_only = flagged_only
        return ns

    def _make_store(self, entries):
        store = MagicMock()
        store.all.return_value = entries
        return store

    def test_prints_report(self, capsys):
        entries = [_make_entry(ts=_ts(i)) for i in range(3)]
        store = self._make_store(entries)
        cmd_ratelimit(self._args(), store)
        out = capsys.readouterr().out
        assert "Rate-limit analysis" in out

    def test_flagged_only_filters(self, capsys):
        # slow traffic — should not appear with flagged_only
        entries = [_make_entry(ts=_ts(i * 5)) for i in range(3)]
        store = self._make_store(entries)
        cmd_ratelimit(self._args(flagged_only=True), store)
        out = capsys.readouterr().out
        assert "No hosts exceeded" in out
