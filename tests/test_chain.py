"""Tests for reqtrace.chain."""

from unittest.mock import MagicMock, patch
import pytest

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.chain import ChainStep, ChainStepResult, ChainResult, run_chain
from reqtrace.replay import ReplayError


def _make_entry(entry_id: str, method: str = "GET", url: str = "http://example.com/") -> RequestLogEntry:
    req = HttpRequest(method=method, url=url, headers={}, body=None)
    resp = HttpResponse(status_code=200, headers={}, body="ok")
    return RequestLogEntry(id=entry_id, request=req, response=resp, timestamp="2024-01-01T00:00:00")


def _make_store(*entries) -> LogStore:
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


class TestChainStepResult:
    def test_str_success(self):
        r = ChainStepResult(entry_id="abc", success=True, status_code=200)
        assert "OK" in str(r)
        assert "200" in str(r)

    def test_str_failure(self):
        r = ChainStepResult(entry_id="abc", success=False, error="timeout")
        assert "FAIL" in str(r)
        assert "timeout" in str(r)


class TestChainResult:
    def test_all_passed_true_when_no_failures(self):
        cr = ChainResult(steps=[ChainStepResult("a", True, 200), ChainStepResult("b", True, 201)])
        assert cr.all_passed is True

    def test_all_passed_false_when_any_failure(self):
        cr = ChainResult(steps=[ChainStepResult("a", True, 200), ChainStepResult("b", False, error="err")])
        assert cr.all_passed is False

    def test_failed_count(self):
        cr = ChainResult(steps=[ChainStepResult("a", False, error="e"), ChainStepResult("b", False, error="e")])
        assert cr.failed_count == 2

    def test_summary_contains_counts(self):
        cr = ChainResult(steps=[ChainStepResult("a", True, 200)])
        summary = cr.summary()
        assert "1/1" in summary


class TestRunChain:
    def _fake_response(self, status_code=200):
        resp = MagicMock()
        resp.status_code = status_code
        return resp

    def test_single_step_success(self):
        entry = _make_entry("id1")
        store = _make_store(entry)
        with patch("reqtrace.chain.replay_request", return_value=self._fake_response(200)):
            result = run_chain(store, [ChainStep(entry_id="id1")])
        assert result.all_passed
        assert result.steps[0].status_code == 200

    def test_missing_entry_marks_failure(self):
        store = _make_store()
        result = run_chain(store, [ChainStep(entry_id="missing")])
        assert not result.all_passed
        assert "not found" in result.steps[0].error

    def test_stop_on_error_halts_chain(self):
        e1 = _make_entry("id1")
        e2 = _make_entry("id2")
        store = _make_store(e1, e2)
        with patch("reqtrace.chain.replay_request", side_effect=ReplayError("conn refused")):
            result = run_chain(store, [
                ChainStep(entry_id="id1", stop_on_error=True),
                ChainStep(entry_id="id2"),
            ])
        assert len(result.steps) == 1
        assert not result.steps[0].success

    def test_continue_on_error_runs_all_steps(self):
        e1 = _make_entry("id1")
        e2 = _make_entry("id2")
        store = _make_store(e1, e2)
        responses = [ReplayError("fail"), self._fake_response(200)]
        with patch("reqtrace.chain.replay_request", side_effect=responses):
            result = run_chain(store, [
                ChainStep(entry_id="id1", stop_on_error=False),
                ChainStep(entry_id="id2", stop_on_error=False),
            ])
        assert len(result.steps) == 2
        assert not result.steps[0].success
        assert result.steps[1].success

    def test_override_host_passed_to_replay(self):
        entry = _make_entry("id1")
        store = _make_store(entry)
        with patch("reqtrace.chain.replay_request", return_value=self._fake_response(201)) as mock_replay:
            run_chain(store, [ChainStep(entry_id="id1", override_host="localhost:9000")])
        mock_replay.assert_called_once_with(entry, override_host="localhost:9000")
