"""Tests for reqtrace.label"""

from __future__ import annotations

import pytest

from reqtrace.models import HttpRequest, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace import label as label_mod


def _make_entry(entry_id: str = "abc", method: str = "GET",
                url: str = "http://example.com/") -> RequestLogEntry:
    req = HttpRequest(method=method, url=url, headers={}, body=None)
    return RequestLogEntry(id=entry_id, timestamp="2024-01-01T00:00:00",
                           request=req, response=None, metadata={})


def _make_store(*entries) -> LogStore:
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


class TestAddLabel:
    def test_add_label_to_existing_entry(self):
        store = _make_store(_make_entry("e1"))
        label_mod.add_label(store, "e1", "auth-flow")
        assert "auth-flow" in label_mod.get_labels(store, "e1")

    def test_add_label_normalises_to_lowercase(self):
        store = _make_store(_make_entry("e1"))
        label_mod.add_label(store, "e1", "Auth-Flow")
        assert "auth-flow" in label_mod.get_labels(store, "e1")

    def test_add_label_replaces_spaces_with_dashes(self):
        store = _make_store(_make_entry("e1"))
        label_mod.add_label(store, "e1", "my label")
        assert "my-label" in label_mod.get_labels(store, "e1")

    def test_add_label_idempotent(self):
        store = _make_store(_make_entry("e1"))
        label_mod.add_label(store, "e1", "dup")
        label_mod.add_label(store, "e1", "dup")
        assert label_mod.get_labels(store, "e1").count("dup") == 1

    def test_add_label_raises_for_missing_entry(self):
        store = LogStore()
        with pytest.raises(KeyError):
            label_mod.add_label(store, "nope", "x")


class TestRemoveLabel:
    def test_remove_existing_label(self):
        store = _make_store(_make_entry("e1"))
        label_mod.add_label(store, "e1", "keep")
        label_mod.add_label(store, "e1", "drop")
        label_mod.remove_label(store, "e1", "drop")
        labels = label_mod.get_labels(store, "e1")
        assert "drop" not in labels
        assert "keep" in labels

    def test_remove_nonexistent_label_is_noop(self):
        store = _make_store(_make_entry("e1"))
        label_mod.remove_label(store, "e1", "ghost")  # should not raise

    def test_remove_raises_for_missing_entry(self):
        store = LogStore()
        with pytest.raises(KeyError):
            label_mod.remove_label(store, "nope", "x")


class TestFilterByLabel:
    def test_returns_matching_entries(self):
        e1 = _make_entry("e1")
        e2 = _make_entry("e2")
        store = _make_store(e1, e2)
        label_mod.add_label(store, "e1", "target")
        result = label_mod.filter_by_label(store, "target")
        assert len(result) == 1
        assert result[0].id == "e1"

    def test_empty_when_no_match(self):
        store = _make_store(_make_entry("e1"))
        assert label_mod.filter_by_label(store, "missing") == []


class TestListAllLabels:
    def test_returns_sorted_unique_labels(self):
        e1 = _make_entry("e1")
        e2 = _make_entry("e2")
        store = _make_store(e1, e2)
        label_mod.add_label(store, "e1", "zebra")
        label_mod.add_label(store, "e2", "alpha")
        label_mod.add_label(store, "e1", "alpha")
        all_labels = label_mod.list_all_labels(store)
        assert all_labels == ["alpha", "zebra"]

    def test_empty_store_returns_empty(self):
        assert label_mod.list_all_labels(LogStore()) == []
