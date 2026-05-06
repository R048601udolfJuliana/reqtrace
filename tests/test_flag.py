"""Tests for reqtrace.flag."""
from __future__ import annotations

import pytest

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.flag import (
    flag_entry,
    unflag_entry,
    is_flagged,
    get_flag_reason,
    list_flagged,
)


def _make_entry(entry_id: str = "abc123") -> RequestLogEntry:
    req = HttpRequest(method="GET", url="http://example.com/api", headers={}, body=None)
    resp = HttpResponse(status_code=200, headers={}, body="ok")
    return RequestLogEntry(id=entry_id, request=req, response=resp, timestamp="2024-01-01T00:00:00")


def _make_store(*ids: str) -> LogStore:
    store = LogStore()
    for eid in ids:
        store.add(_make_entry(eid))
    return store


class TestFlagEntry:
    def test_flag_adds_metadata(self):
        store = _make_store("e1")
        entry = flag_entry(store, "e1")
        assert entry.metadata.get("flagged") is True

    def test_flag_adds_flagged_tag(self):
        store = _make_store("e1")
        flag_entry(store, "e1")
        entry = store.get_by_id("e1")
        assert "flagged" in entry.metadata.get("tags", [])

    def test_flag_idempotent(self):
        store = _make_store("e1")
        flag_entry(store, "e1")
        flag_entry(store, "e1")
        entry = store.get_by_id("e1")
        assert entry.metadata["tags"].count("flagged") == 1

    def test_flag_stores_reason(self):
        store = _make_store("e1")
        entry = flag_entry(store, "e1", reason="needs review")
        assert get_flag_reason(entry) == "needs review"

    def test_flag_raises_for_missing_entry(self):
        store = LogStore()
        with pytest.raises(KeyError):
            flag_entry(store, "missing")


class TestUnflagEntry:
    def test_unflag_removes_metadata(self):
        store = _make_store("e1")
        flag_entry(store, "e1", reason="old")
        unflag_entry(store, "e1")
        entry = store.get_by_id("e1")
        assert not is_flagged(entry)
        assert get_flag_reason(entry) == ""

    def test_unflag_removes_tag(self):
        store = _make_store("e1")
        flag_entry(store, "e1")
        unflag_entry(store, "e1")
        entry = store.get_by_id("e1")
        assert "flagged" not in entry.metadata.get("tags", [])

    def test_unflag_raises_for_missing_entry(self):
        store = LogStore()
        with pytest.raises(KeyError):
            unflag_entry(store, "missing")


class TestIsFlagged:
    def test_not_flagged_by_default(self):
        entry = _make_entry()
        assert not is_flagged(entry)

    def test_flagged_after_flag_call(self):
        store = _make_store("e1")
        entry = flag_entry(store, "e1")
        assert is_flagged(entry)


class TestListFlagged:
    def test_empty_store_returns_empty(self):
        assert list_flagged(LogStore()) == []

    def test_returns_only_flagged(self):
        store = _make_store("e1", "e2", "e3")
        flag_entry(store, "e1")
        flag_entry(store, "e3")
        result = list_flagged(store)
        ids = {e.id for e in result}
        assert ids == {"e1", "e3"}
