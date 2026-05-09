"""Tests for reqtrace.severity."""

from __future__ import annotations

import pytest

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.severity import (
    SeverityError,
    clear_severity,
    filter_by_severity,
    get_severity,
    list_by_severity,
    set_severity,
)


def _make_entry(entry_id: str = "abc123", method: str = "GET", url: str = "http://example.com") -> RequestLogEntry:
    req = HttpRequest(method=method, url=url, headers={}, body=None)
    return RequestLogEntry(id=entry_id, timestamp="2024-01-01T00:00:00Z", request=req, response=None)


def _make_store(*entries: RequestLogEntry) -> LogStore:
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


class TestSetSeverity:
    def test_sets_severity_on_entry(self):
        entry = _make_entry()
        set_severity(entry, "high")
        assert entry.metadata["severity"] == "high"

    def test_normalises_to_lowercase(self):
        entry = _make_entry()
        set_severity(entry, "CRITICAL")
        assert entry.metadata["severity"] == "critical"

    def test_adds_severity_tag(self):
        entry = _make_entry()
        set_severity(entry, "medium")
        assert "severity:medium" in entry.metadata["tags"]

    def test_replaces_existing_severity_tag(self):
        entry = _make_entry()
        set_severity(entry, "low")
        set_severity(entry, "high")
        tags = entry.metadata["tags"]
        severity_tags = [t for t in tags if t.startswith("severity:")]
        assert severity_tags == ["severity:high"]

    def test_raises_on_invalid_level(self):
        entry = _make_entry()
        with pytest.raises(SeverityError):
            set_severity(entry, "extreme")


class TestGetSeverity:
    def test_returns_none_when_not_set(self):
        entry = _make_entry()
        assert get_severity(entry) is None

    def test_returns_set_level(self):
        entry = _make_entry()
        set_severity(entry, "low")
        assert get_severity(entry) == "low"


class TestClearSeverity:
    def test_removes_metadata_key(self):
        entry = _make_entry()
        set_severity(entry, "high")
        clear_severity(entry)
        assert "severity" not in entry.metadata

    def test_removes_severity_tag(self):
        entry = _make_entry()
        set_severity(entry, "high")
        clear_severity(entry)
        assert not any(t.startswith("severity:") for t in entry.metadata.get("tags", []))

    def test_clear_on_entry_without_severity_is_safe(self):
        entry = _make_entry()
        clear_severity(entry)  # should not raise


class TestFilterBySeverity:
    def test_returns_matching_entries(self):
        e1 = _make_entry("id1")
        e2 = _make_entry("id2")
        set_severity(e1, "high")
        set_severity(e2, "low")
        store = _make_store(e1, e2)
        result = filter_by_severity(store, "high")
        assert len(result) == 1
        assert result[0].id == "id1"

    def test_empty_when_no_match(self):
        entry = _make_entry()
        set_severity(entry, "low")
        store = _make_store(entry)
        assert filter_by_severity(store, "critical") == []

    def test_raises_on_invalid_level(self):
        store = _make_store()
        with pytest.raises(SeverityError):
            filter_by_severity(store, "unknown")


class TestListBySeverity:
    def test_groups_entries_by_level(self):
        e1 = _make_entry("id1")
        e2 = _make_entry("id2")
        e3 = _make_entry("id3")
        set_severity(e1, "high")
        set_severity(e2, "high")
        set_severity(e3, "low")
        store = _make_store(e1, e2, e3)
        grouped = list_by_severity(store)
        assert len(grouped["high"]) == 2
        assert len(grouped["low"]) == 1
        assert grouped["medium"] == []

    def test_untagged_entries_not_included(self):
        entry = _make_entry()
        store = _make_store(entry)
        grouped = list_by_severity(store)
        assert all(len(v) == 0 for v in grouped.values())
