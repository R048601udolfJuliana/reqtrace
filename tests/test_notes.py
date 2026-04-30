"""Tests for reqtrace.notes module."""

import pytest

from reqtrace.models import HttpRequest, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.notes import (
    add_note,
    get_notes,
    clear_notes,
    list_entries_with_notes,
    NOTES_KEY,
)


def _make_entry(entry_id="abc123"):
    req = HttpRequest(method="GET", url="http://example.com/", headers={}, body=None)
    return RequestLogEntry(id=entry_id, timestamp="2024-01-01T00:00:00", request=req)


def _make_store(*entries):
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


class TestAddNote:
    def test_add_single_note(self):
        store = _make_store(_make_entry())
        add_note(store, "abc123", "first note")
        notes = get_notes(store, "abc123")
        assert notes == ["first note"]

    def test_add_multiple_notes(self):
        store = _make_store(_make_entry())
        add_note(store, "abc123", "note one")
        add_note(store, "abc123", "note two")
        notes = get_notes(store, "abc123")
        assert len(notes) == 2
        assert "note one" in notes
        assert "note two" in notes

    def test_add_note_strips_whitespace(self):
        store = _make_store(_make_entry())
        add_note(store, "abc123", "  trimmed  ")
        assert get_notes(store, "abc123") == ["trimmed"]

    def test_add_note_raises_on_missing_entry(self):
        store = LogStore()
        with pytest.raises(KeyError):
            add_note(store, "missing", "note")

    def test_add_empty_note_raises(self):
        store = _make_store(_make_entry())
        with pytest.raises(ValueError):
            add_note(store, "abc123", "   ")


class TestGetNotes:
    def test_returns_empty_list_when_no_notes(self):
        store = _make_store(_make_entry())
        assert get_notes(store, "abc123") == []

    def test_raises_on_missing_entry(self):
        store = LogStore()
        with pytest.raises(KeyError):
            get_notes(store, "nope")


class TestClearNotes:
    def test_clear_removes_all_notes(self):
        store = _make_store(_make_entry())
        add_note(store, "abc123", "note")
        clear_notes(store, "abc123")
        assert get_notes(store, "abc123") == []

    def test_clear_on_entry_without_notes_is_safe(self):
        store = _make_store(_make_entry())
        clear_notes(store, "abc123")  # should not raise

    def test_clear_raises_on_missing_entry(self):
        store = LogStore()
        with pytest.raises(KeyError):
            clear_notes(store, "ghost")


class TestListEntriesWithNotes:
    def test_empty_store(self):
        assert list_entries_with_notes(LogStore()) == []

    def test_no_entries_have_notes(self):
        store = _make_store(_make_entry("a"), _make_entry("b"))
        assert list_entries_with_notes(store) == []

    def test_only_annotated_entries_returned(self):
        store = _make_store(_make_entry("a"), _make_entry("b"))
        add_note(store, "a", "important")
        result = list_entries_with_notes(store)
        assert len(result) == 1
        assert result[0].id == "a"
