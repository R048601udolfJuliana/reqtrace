"""Tests for reqtrace.stats module."""
import pytest
from datetime import datetime
from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.stats import compute_stats, format_stats


def _make_entry(method="GET", url="http://example.com/api", status=200, body="ok"):
    req = HttpRequest(method=method, url=url, headers={}, body=None)
    resp = HttpResponse(status_code=status, headers={}, body=body)
    return RequestLogEntry(
        entry_id="test-id",
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        request=req,
        response=resp,
    )


class TestComputeStats:
    def test_empty_returns_zeros(self):
        stats = compute_stats([])
        assert stats["total"] == 0
        assert stats["error_rate"] == 0.0
        assert stats["avg_response_size"] == 0.0
        assert stats["methods"] == {}
        assert stats["status_codes"] == {}

    def test_single_entry(self):
        stats = compute_stats([_make_entry()])
        assert stats["total"] == 1
        assert stats["methods"] == {"GET": 1}
        assert stats["status_codes"] == {200: 1}
        assert stats["error_rate"] == 0.0

    def test_counts_methods(self):
        entries = [
            _make_entry(method="GET"),
            _make_entry(method="POST"),
            _make_entry(method="GET"),
        ]
        stats = compute_stats(entries)
        assert stats["methods"]["GET"] == 2
        assert stats["methods"]["POST"] == 1

    def test_error_rate_with_4xx(self):
        entries = [
            _make_entry(status=200),
            _make_entry(status=404),
            _make_entry(status=500),
        ]
        stats = compute_stats(entries)
        assert stats["error_rate"] == pytest.approx(2 / 3, rel=1e-3)

    def test_no_response_counts_as_error(self):
        req = HttpRequest(method="GET", url="http://example.com", headers={}, body=None)
        entry = RequestLogEntry(
            entry_id="x",
            timestamp=datetime(2024, 1, 1),
            request=req,
            response=None,
        )
        stats = compute_stats([entry])
        assert stats["error_rate"] == 1.0
        assert stats["status_codes"]["no_response"] == 1

    def test_avg_response_size(self):
        entries = [
            _make_entry(body="ab"),    # 2 bytes
            _make_entry(body="abcd"),  # 4 bytes
        ]
        stats = compute_stats(entries)
        assert stats["avg_response_size"] == 3.0

    def test_hosts_counted(self):
        entries = [
            _make_entry(url="http://api.example.com/foo"),
            _make_entry(url="http://api.example.com/bar"),
            _make_entry(url="http://other.com/baz"),
        ]
        stats = compute_stats(entries)
        assert stats["hosts"]["api.example.com"] == 2
        assert stats["hosts"]["other.com"] == 1


class TestFormatStats:
    def test_format_contains_total(self):
        stats = compute_stats([_make_entry()])
        output = format_stats(stats)
        assert "Total requests" in output
        assert "1" in output

    def test_format_contains_method(self):
        stats = compute_stats([_make_entry(method="DELETE")])
        output = format_stats(stats)
        assert "DELETE" in output

    def test_format_contains_error_rate(self):
        entries = [_make_entry(status=500), _make_entry(status=200)]
        stats = compute_stats(entries)
        output = format_stats(stats)
        assert "Error rate" in output
        assert "50.0%" in output
