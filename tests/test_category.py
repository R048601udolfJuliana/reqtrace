"""Tests for reqtrace.category."""

from __future__ import annotations

import pytest

from reqtrace.models import HttpRequest, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.category import (
    CategoryError,
    clear_category,
    filter_by_category,
    get_category,
    list_categories,
    set_category,
)


def _make_entry(entry_id: str = "e1", url: str = "http://example.com/") -> RequestLogEntry:
    req = HttpRequest(method="GET", url=url, headers={}, body=None)
    return RequestLogEntry(id=entry_id, request=req, response=None,
                           timestamp="2024-01-01T00:00:00Z", metadata={})


def _make_store(*entries: RequestLogEntry) -> LogStore:
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


class TestSetCategory:
    def test_sets_category_on_entry(self):
        entry = _make_entry()
        set_category(entry, "auth")
        assert entry.metadata["category"] == "auth"

    def test_normalises_to_lowercase(self):
        entry = _make_entry()
        set_category(entry, "  Billing  ")
        assert entry.metadata["category"] == "billing"

    def test_overwrites_existing_category(self):
        entry = _make_entry()
        set_category(entry, "auth")
        set_category(entry, "search")
        assert entry.metadata["category"] == "search"

    def test_empty_string_raises(self):
        entry = _make_entry()
        with pytest.raises(CategoryError):
            set_category(entry, "   ")


class TestGetCategory:
    def test_returns_none_when_not_set(self):
        entry = _make_entry()
        assert get_category(entry) is None

    def test_returns_set_category(self):
        entry = _make_entry()
        set_category(entry, "payments")
        assert get_category(entry) == "payments"


class TestClearCategory:
    def test_removes_existing_category(self):
        entry = _make_entry()
        set_category(entry, "auth")
        clear_category(entry)
        assert get_category(entry) is None

    def test_clear_when_not_set_is_safe(self):
        entry = _make_entry()
        clear_category(entry)  # should not raise
        assert get_category(entry) is None


class TestFilterByCategory:
    def test_returns_matching_entries(self):
        e1, e2, e3 = _make_entry("e1"), _make_entry("e2"), _make_entry("e3")
        set_category(e1, "auth")
        set_category(e2, "billing")
        set_category(e3, "auth")
        store = _make_store(e1, e2, e3)
        result = filter_by_category(store, "auth")
        assert {e.id for e in result} == {"e1", "e3"}

    def test_returns_empty_when_no_match(self):
        entry = _make_entry()
        set_category(entry, "auth")
        store = _make_store(entry)
        assert filter_by_category(store, "billing") == []

    def test_normalises_query(self):
        entry = _make_entry()
        set_category(entry, "search")
        store = _make_store(entry)
        assert filter_by_category(store, "  SEARCH  ") == [entry]


class TestListCategories:
    def test_empty_store_returns_empty(self):
        assert list_categories(_make_store()) == []

    def test_returns_sorted_unique_categories(self):
        e1, e2, e3 = _make_entry("e1"), _make_entry("e2"), _make_entry("e3")
        set_category(e1, "search")
        set_category(e2, "auth")
        set_category(e3, "search")
        store = _make_store(e1, e2, e3)
        assert list_categories(store) == ["auth", "search"]

    def test_entries_without_category_excluded(self):
        e1, e2 = _make_entry("e1"), _make_entry("e2")
        set_category(e1, "billing")
        store = _make_store(e1, e2)
        assert list_categories(store) == ["billing"]
