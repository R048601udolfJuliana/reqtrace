"""Tests for reqtrace.priority."""

from __future__ import annotations

import pytest

from reqtrace.models import HttpRequest, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.priority import (
    HIGH,
    LOW,
    MEDIUM,
    PriorityError,
    filter_by_priority,
    get_priority,
    list_by_priority,
    priority_label,
    set_priority,
)


def _make_entry(entry_id: str = "abc", method: str = "GET", url: str = "http://example.com") -> RequestLogEntry:
    req = HttpRequest(method=method, url=url, headers={}, body=None)
    return RequestLogEntry(entry_id=entry_id, request=req, response=None)


def _make_store(*entries: RequestLogEntry) -> LogStore:
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


class TestSetPriority:
    def test_sets_priority_on_entry(self):
        store = _make_store(_make_entry("1"))
        entry = set_priority(store, "1", HIGH)
        assert entry.metadata["priority"] == HIGH

    def test_overwrites_existing_priority(self):
        store = _make_store(_make_entry("1"))
        set_priority(store, "1", LOW)
        entry = set_priority(store, "1", MEDIUM)
        assert entry.metadata["priority"] == MEDIUM

    def test_raises_for_invalid_level(self):
        store = _make_store(_make_entry("1"))
        with pytest.raises(PriorityError):
            set_priority(store, "1", 99)

    def test_raises_for_missing_entry(self):
        store = LogStore()
        with pytest.raises(KeyError):
            set_priority(store, "missing", HIGH)


class TestGetPriority:
    def test_returns_none_when_unset(self):
        entry = _make_entry()
        assert get_priority(entry) is None

    def test_returns_set_level(self):
        entry = _make_entry()
        entry.metadata["priority"] = LOW
        assert get_priority(entry) == LOW


class TestPriorityLabel:
    def test_none_when_unset(self):
        assert priority_label(_make_entry()) == "none"

    def test_low_label(self):
        e = _make_entry()
        e.metadata["priority"] = LOW
        assert priority_label(e) == "low"

    def test_medium_label(self):
        e = _make_entry()
        e.metadata["priority"] = MEDIUM
        assert priority_label(e) == "medium"

    def test_high_label(self):
        e = _make_entry()
        e.metadata["priority"] = HIGH
        assert priority_label(e) == "high"


class TestFilterByPriority:
    def test_returns_matching_entries(self):
        e1, e2, e3 = _make_entry("1"), _make_entry("2"), _make_entry("3")
        e1.metadata["priority"] = HIGH
        e2.metadata["priority"] = LOW
        e3.metadata["priority"] = HIGH
        result = filter_by_priority([e1, e2, e3], HIGH)
        assert result == [e1, e3]

    def test_empty_when_no_match(self):
        e = _make_entry()
        e.metadata["priority"] = LOW
        assert filter_by_priority([e], HIGH) == []

    def test_raises_for_invalid_level(self):
        with pytest.raises(PriorityError):
            filter_by_priority([], 0)


class TestListByPriority:
    def test_excludes_entries_without_priority(self):
        e = _make_entry("1")
        store = _make_store(e)
        assert list_by_priority(store) == []

    def test_sorted_high_to_low(self):
        e1, e2, e3 = _make_entry("1"), _make_entry("2"), _make_entry("3")
        e1.metadata["priority"] = LOW
        e2.metadata["priority"] = HIGH
        e3.metadata["priority"] = MEDIUM
        store = _make_store(e1, e2, e3)
        result = list_by_priority(store)
        assert [get_priority(e) for e in result] == [HIGH, MEDIUM, LOW]
