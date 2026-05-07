"""Tests for reqtrace.remind."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest

from reqtrace.models import HttpRequest, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.remind import (
    ReminderError,
    clear_reminder,
    get_reminder,
    is_due,
    list_due,
    set_reminder,
)


def _make_entry(entry_id: str = "abc123") -> RequestLogEntry:
    req = HttpRequest(method="GET", url="http://example.com/", headers={}, body=None)
    return RequestLogEntry(
        id=entry_id,
        timestamp="2024-01-01T00:00:00+00:00",
        request=req,
        response=None,
        metadata={},
    )


def _make_store(*entries) -> LogStore:
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


class TestSetReminder:
    def test_sets_remind_at_in_metadata(self):
        store = _make_store(_make_entry())
        set_reminder(store, "abc123", 30)
        entry = store.get_by_id("abc123")
        assert "remind_at" in entry.metadata

    def test_remind_at_is_in_the_future(self):
        store = _make_store(_make_entry())
        before = datetime.now(timezone.utc)
        set_reminder(store, "abc123", 10)
        remind_at = get_reminder(store.get_by_id("abc123"))
        assert remind_at > before

    def test_note_stored_when_provided(self):
        store = _make_store(_make_entry())
        set_reminder(store, "abc123", 5, note="check this later")
        entry = store.get_by_id("abc123")
        assert entry.metadata["remind_note"] == "check this later"

    def test_note_cleared_when_empty(self):
        store = _make_store(_make_entry())
        entry = store.get_by_id("abc123")
        entry.metadata["remind_note"] = "old note"
        store.update(entry)
        set_reminder(store, "abc123", 5, note="")
        assert "remind_note" not in store.get_by_id("abc123").metadata

    def test_raises_for_missing_entry(self):
        store = _make_store()
        with pytest.raises(ReminderError, match="not found"):
            set_reminder(store, "nope", 10)

    def test_raises_for_non_positive_minutes(self):
        store = _make_store(_make_entry())
        with pytest.raises(ReminderError, match="positive"):
            set_reminder(store, "abc123", 0)


class TestClearReminder:
    def test_removes_remind_at(self):
        store = _make_store(_make_entry())
        set_reminder(store, "abc123", 15)
        clear_reminder(store, "abc123")
        assert get_reminder(store.get_by_id("abc123")) is None

    def test_removes_note(self):
        store = _make_store(_make_entry())
        set_reminder(store, "abc123", 15, note="hi")
        clear_reminder(store, "abc123")
        assert "remind_note" not in store.get_by_id("abc123").metadata

    def test_raises_for_missing_entry(self):
        store = _make_store()
        with pytest.raises(ReminderError):
            clear_reminder(store, "ghost")


class TestIsDue:
    def test_not_due_when_in_future(self):
        entry = _make_entry()
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        entry.metadata["remind_at"] = future.isoformat()
        assert not is_due(entry)

    def test_due_when_in_past(self):
        entry = _make_entry()
        past = datetime.now(timezone.utc) - timedelta(seconds=1)
        entry.metadata["remind_at"] = past.isoformat()
        assert is_due(entry)

    def test_not_due_when_no_reminder(self):
        assert not is_due(_make_entry())


class TestListDue:
    def test_returns_only_due_entries(self):
        e1 = _make_entry("e1")
        e2 = _make_entry("e2")
        past = datetime.now(timezone.utc) - timedelta(minutes=1)
        future = datetime.now(timezone.utc) + timedelta(minutes=60)
        e1.metadata["remind_at"] = past.isoformat()
        e2.metadata["remind_at"] = future.isoformat()
        store = _make_store(e1, e2)
        due = list_due(store)
        assert len(due) == 1
        assert due[0].id == "e1"

    def test_empty_when_no_reminders(self):
        store = _make_store(_make_entry("x"), _make_entry("y"))
        assert list_due(store) == []
