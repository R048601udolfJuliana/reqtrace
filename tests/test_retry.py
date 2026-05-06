"""Tests for reqtrace.retry."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.replay import ReplayError
from reqtrace.retry import RetryPolicy, RetryResult, retry_entry


def _make_entry(method: str = "GET", url: str = "http://example.com/") -> RequestLogEntry:
    req = HttpRequest(method=method, url=url, headers={}, body=None)
    return RequestLogEntry(request=req)


def _response(status: int) -> HttpResponse:
    return HttpResponse(status_code=status, headers={}, body=None)


class TestRetryEntry:
    def _no_sleep(self, _seconds: float) -> None:
        pass

    def test_success_on_first_attempt(self):
        entry = _make_entry()
        policy = RetryPolicy(max_attempts=3)
        with patch("reqtrace.retry.replay_request", return_value=_response(200)) as mock_replay:
            result = retry_entry(entry, policy, sleep_fn=self._no_sleep)
        assert result.success is True
        assert result.attempts == 1
        assert result.final_status == 200
        mock_replay.assert_called_once()

    def test_retries_on_500_then_succeeds(self):
        entry = _make_entry()
        policy = RetryPolicy(max_attempts=3)
        responses = [_response(500), _response(200)]
        with patch("reqtrace.retry.replay_request", side_effect=responses):
            result = retry_entry(entry, policy, sleep_fn=self._no_sleep)
        assert result.success is True
        assert result.attempts == 2
        assert result.final_status == 200

    def test_exhausts_all_attempts(self):
        entry = _make_entry()
        policy = RetryPolicy(max_attempts=3)
        with patch("reqtrace.retry.replay_request", return_value=_response(503)):
            result = retry_entry(entry, policy, sleep_fn=self._no_sleep)
        assert result.success is False
        assert result.attempts == 3
        assert result.final_status == 503

    def test_replay_error_counts_as_failure(self):
        entry = _make_entry()
        policy = RetryPolicy(max_attempts=2)
        with patch("reqtrace.retry.replay_request", side_effect=ReplayError("conn refused")):
            result = retry_entry(entry, policy, sleep_fn=self._no_sleep)
        assert result.success is False
        assert result.error == "conn refused"
        assert result.final_status is None

    def test_non_retry_status_succeeds_immediately(self):
        entry = _make_entry()
        policy = RetryPolicy(max_attempts=5, retry_on_status=[500])
        with patch("reqtrace.retry.replay_request", return_value=_response(404)):
            result = retry_entry(entry, policy, sleep_fn=self._no_sleep)
        assert result.success is True
        assert result.attempts == 1

    def test_sleep_called_between_attempts(self):
        entry = _make_entry()
        policy = RetryPolicy(max_attempts=3, backoff_base=2.0)
        sleep_calls: list[float] = []
        with patch("reqtrace.retry.replay_request", return_value=_response(500)):
            retry_entry(entry, policy, sleep_fn=lambda s: sleep_calls.append(s))
        # sleep is called after each failed attempt except the last
        assert sleep_calls == [2.0, 4.0]

    def test_override_host_forwarded_to_replay(self):
        entry = _make_entry()
        policy = RetryPolicy(max_attempts=1, override_host="localhost:9000")
        with patch("reqtrace.retry.replay_request", return_value=_response(200)) as mock_replay:
            retry_entry(entry, policy, sleep_fn=self._no_sleep)
        _, kwargs = mock_replay.call_args
        assert kwargs.get("override_host") == "localhost:9000"
