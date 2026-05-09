"""Tests for reqtrace.milestone."""

from __future__ import annotations

import pytest

from reqtrace.models import HttpRequest, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace import milestone as ms


def _make_entry(entry_id: str = "abc123") -> RequestLogEntry:
    req = HttpRequest(method="GET", url="http://example.com/api", headers={}, body=None)
    return RequestLogEntry(id=entry_id, timestamp="2024-01-01T00:00:00Z", request=req)


def _make_store(*ids: str) -> LogStore:
    store = LogStore()
    for eid in ids:
        store.add(_make_entry(eid))
    return store


class TestSetMilestone:
    def test_sets_milestone_name(self):
        store = _make_store("e1")
        ms.set_milestone(store, "e1", "v1.0 release")
        assert ms.get_milestone(store, "e1") == "v1.0 release"

    def test_strips_whitespace_from_name(self):
        store = _make_store("e1")
        ms.set_milestone(store, "e1", "  beta  ")
        assert ms.get_milestone(store, "e1") == "beta"

    def test_raises_on_empty_name(self):
        store = _make_store("e1")
        with pytest.raises(ms.MilestoneError, match="empty"):
            ms.set_milestone(store, "e1", "   ")

    def test_raises_when_entry_not_found(self):
        store = _make_store()
        with pytest.raises(ms.MilestoneError, match="not found"):
            ms.set_milestone(store, "missing", "v2")

    def test_default_reached_is_false(self):
        store = _make_store("e1")
        ms.set_milestone(store, "e1", "alpha")
        assert ms.is_reached(store, "e1") is False


class TestMarkReached:
    def test_marks_milestone_reached(self):
        store = _make_store("e1")
        ms.set_milestone(store, "e1", "launch")
        ms.mark_reached(store, "e1")
        assert ms.is_reached(store, "e1") is True

    def test_raises_when_no_milestone_set(self):
        store = _make_store("e1")
        with pytest.raises(ms.MilestoneError, match="no milestone"):
            ms.mark_reached(store, "e1")

    def test_raises_when_entry_not_found(self):
        store = _make_store()
        with pytest.raises(ms.MilestoneError, match="not found"):
            ms.mark_reached(store, "ghost")


class TestClearMilestone:
    def test_removes_milestone_metadata(self):
        store = _make_store("e1")
        ms.set_milestone(store, "e1", "checkpoint")
        ms.clear_milestone(store, "e1")
        assert ms.get_milestone(store, "e1") is None

    def test_clear_on_entry_without_milestone_is_safe(self):
        store = _make_store("e1")
        ms.clear_milestone(store, "e1")  # should not raise

    def test_raises_when_entry_not_found(self):
        store = _make_store()
        with pytest.raises(ms.MilestoneError, match="not found"):
            ms.clear_milestone(store, "nope")


class TestListMilestones:
    def test_empty_store_returns_empty(self):
        store = _make_store()
        assert ms.list_milestones(store) == []

    def test_returns_entry_with_milestone(self):
        store = _make_store("e1", "e2")
        ms.set_milestone(store, "e1", "v1")
        items = ms.list_milestones(store)
        assert len(items) == 1
        assert items[0]["id"] == "e1"
        assert items[0]["milestone"] == "v1"
        assert items[0]["reached"] is False

    def test_reached_flag_reflected_in_list(self):
        store = _make_store("e1")
        ms.set_milestone(store, "e1", "done")
        ms.mark_reached(store, "e1")
        items = ms.list_milestones(store)
        assert items[0]["reached"] is True

    def test_entries_without_milestone_excluded(self):
        store = _make_store("e1", "e2", "e3")
        ms.set_milestone(store, "e2", "mid")
        items = ms.list_milestones(store)
        ids = [i["id"] for i in items]
        assert ids == ["e2"]
