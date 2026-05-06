"""Tests for reqtrace.pin module."""

from __future__ import annotations

import pytest

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.pin import pin_entry, unpin_entry, is_pinned, list_pinned, PIN_TAG


def _make_entry(entry_id="abc123", method="GET", url="http://example.com/", status=200):
    req = HttpRequest(method=method, url=url, headers={}, body=None)
    resp = HttpResponse(status_code=status, headers={}, body=None)
    entry = RequestLogEntry(request=req, response=resp)
    entry.id = entry_id
    return entry


def _make_store(*entries):
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


class TestPinEntry:
    def test_pin_adds_pinned_metadata(self):
        entry = _make_entry()
        store = _make_store(entry)
        pin_entry(store, entry.id)
        updated = store.get_by_id(entry.id)
        assert updated.metadata.get("pinned") is True

    def test_pin_adds_pinned_tag(self):
        entry = _make_entry()
        store = _make_store(entry)
        pin_entry(store, entry.id)
        updated = store.get_by_id(entry.id)
        assert PIN_TAG in updated.metadata.get("tags", [])

    def test_pin_idempotent(self):
        entry = _make_entry()
        store = _make_store(entry)
        pin_entry(store, entry.id)
        pin_entry(store, entry.id)
        updated = store.get_by_id(entry.id)
        assert updated.metadata["tags"].count(PIN_TAG) == 1

    def test_pin_returns_false_for_missing_id(self):
        store = _make_store()
        result = pin_entry(store, "nonexistent")
        assert result is False

    def test_pin_returns_true_on_success(self):
        entry = _make_entry()
        store = _make_store(entry)
        result = pin_entry(store, entry.id)
        assert result is True


class TestUnpinEntry:
    def test_unpin_removes_pinned_flag(self):
        entry = _make_entry()
        store = _make_store(entry)
        pin_entry(store, entry.id)
        unpin_entry(store, entry.id)
        updated = store.get_by_id(entry.id)
        assert updated.metadata.get("pinned") is False

    def test_unpin_removes_tag(self):
        entry = _make_entry()
        store = _make_store(entry)
        pin_entry(store, entry.id)
        unpin_entry(store, entry.id)
        updated = store.get_by_id(entry.id)
        assert PIN_TAG not in updated.metadata.get("tags", [])

    def test_unpin_returns_false_for_missing(self):
        store = _make_store()
        assert unpin_entry(store, "ghost") is False


class TestIsPinned:
    def test_returns_false_by_default(self):
        entry = _make_entry()
        assert is_pinned(entry) is False

    def test_returns_true_after_pin(self):
        entry = _make_entry()
        store = _make_store(entry)
        pin_entry(store, entry.id)
        updated = store.get_by_id(entry.id)
        assert is_pinned(updated) is True


class TestListPinned:
    def test_empty_when_none_pinned(self):
        store = _make_store(_make_entry("a"), _make_entry("b"))
        assert list_pinned(store) == []

    def test_returns_only_pinned(self):
        e1 = _make_entry("id1")
        e2 = _make_entry("id2")
        store = _make_store(e1, e2)
        pin_entry(store, "id1")
        pinned = list_pinned(store)
        assert len(pinned) == 1
        assert pinned[0].id == "id1"

    def test_returns_multiple_pinned(self):
        entries = [_make_entry(f"id{i}") for i in range(3)]
        store = _make_store(*entries)
        pin_entry(store, "id0")
        pin_entry(store, "id2")
        pinned = list_pinned(store)
        assert len(pinned) == 2
