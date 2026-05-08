"""Tests for reqtrace.verdict."""

import pytest

from reqtrace.models import HttpRequest, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.verdict import (
    VerdictError,
    clear_verdict,
    get_verdict,
    get_verdict_reason,
    list_by_verdict,
    set_verdict,
    verdict_summary,
)


def _make_entry(entry_id: str = "abc", method: str = "GET", url: str = "http://example.com"):
    req = HttpRequest(method=method, url=url, headers={}, body=None)
    return RequestLogEntry(id=entry_id, timestamp="2024-01-01T00:00:00Z", request=req)


def _make_store(*entries):
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


class TestSetVerdict:
    def test_sets_pass_verdict(self):
        entry = _make_entry()
        set_verdict(entry, "pass")
        assert entry.metadata["verdict"] == "pass"

    def test_sets_fail_verdict(self):
        entry = _make_entry()
        set_verdict(entry, "fail")
        assert entry.metadata["verdict"] == "fail"

    def test_sets_skip_verdict(self):
        entry = _make_entry()
        set_verdict(entry, "skip")
        assert entry.metadata["verdict"] == "skip"

    def test_normalises_to_lowercase(self):
        entry = _make_entry()
        set_verdict(entry, "PASS")
        assert entry.metadata["verdict"] == "pass"

    def test_stores_reason_when_provided(self):
        entry = _make_entry()
        set_verdict(entry, "fail", reason="Status code mismatch")
        assert entry.metadata["verdict_reason"] == "Status code mismatch"

    def test_clears_old_reason_when_not_provided(self):
        entry = _make_entry()
        set_verdict(entry, "fail", reason="old reason")
        set_verdict(entry, "pass")
        assert "verdict_reason" not in entry.metadata

    def test_raises_on_invalid_verdict(self):
        entry = _make_entry()
        with pytest.raises(VerdictError):
            set_verdict(entry, "maybe")


class TestGetVerdict:
    def test_returns_none_when_unset(self):
        entry = _make_entry()
        assert get_verdict(entry) is None

    def test_returns_verdict_when_set(self):
        entry = _make_entry()
        set_verdict(entry, "skip")
        assert get_verdict(entry) == "skip"

    def test_get_reason_returns_none_when_absent(self):
        entry = _make_entry()
        set_verdict(entry, "pass")
        assert get_verdict_reason(entry) is None

    def test_get_reason_returns_reason(self):
        entry = _make_entry()
        set_verdict(entry, "fail", reason="timeout")
        assert get_verdict_reason(entry) == "timeout"


class TestClearVerdict:
    def test_removes_verdict(self):
        entry = _make_entry()
        set_verdict(entry, "pass")
        clear_verdict(entry)
        assert get_verdict(entry) is None

    def test_removes_reason_too(self):
        entry = _make_entry()
        set_verdict(entry, "fail", reason="bad")
        clear_verdict(entry)
        assert get_verdict_reason(entry) is None

    def test_clear_on_unset_is_safe(self):
        entry = _make_entry()
        clear_verdict(entry)  # should not raise


class TestListByVerdict:
    def test_returns_matching_entries(self):
        e1 = _make_entry("1")
        e2 = _make_entry("2")
        e3 = _make_entry("3")
        set_verdict(e1, "pass")
        set_verdict(e2, "fail")
        set_verdict(e3, "pass")
        store = _make_store(e1, e2, e3)
        result = list_by_verdict(store, "pass")
        assert len(result) == 2
        assert all(get_verdict(e) == "pass" for e in result)

    def test_empty_when_none_match(self):
        e1 = _make_entry("1")
        set_verdict(e1, "pass")
        store = _make_store(e1)
        assert list_by_verdict(store, "fail") == []


class TestVerdictSummary:
    def test_all_zeros_for_empty_store(self):
        store = _make_store()
        s = verdict_summary(store)
        assert s["pass"] == 0
        assert s["fail"] == 0
        assert s["skip"] == 0
        assert s["unset"] == 0

    def test_counts_correctly(self):
        e1, e2, e3, e4 = (_make_entry(str(i)) for i in range(4))
        set_verdict(e1, "pass")
        set_verdict(e2, "pass")
        set_verdict(e3, "fail")
        # e4 has no verdict
        store = _make_store(e1, e2, e3, e4)
        s = verdict_summary(store)
        assert s["pass"] == 2
        assert s["fail"] == 1
        assert s["skip"] == 0
        assert s["unset"] == 1
