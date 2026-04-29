"""Tests for reqtrace/tags.py"""

import pytest
from datetime import datetime, timezone
from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.tags import add_tag, remove_tag, get_tags, filter_by_tag, list_all_tags


def _make_entry(entry_id: str, method: str = "GET", url: str = "http://example.com") -> RequestLogEntry:
    req = HttpRequest(method=method, url=url, headers={}, body=None)
    return RequestLogEntry(
        entry_id=entry_id,
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        request=req,
        response=None,
        tags=[],
    )


def _make_store(*entries) -> LogStore:
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


class TestAddTag:
    def test_add_tag_to_existing_entry(self):
        entry = _make_entry("abc")
        store = _make_store(entry)
        result = add_tag(store, "abc", "important")
        assert result is True
        assert "important" in entry.tags

    def test_add_tag_normalises_to_lowercase(self):
        entry = _make_entry("abc")
        store = _make_store(entry)
        add_tag(store, "abc", "  URGENT  ")
        assert "urgent" in entry.tags

    def test_add_duplicate_tag_is_idempotent(self):
        entry = _make_entry("abc")
        store = _make_store(entry)
        add_tag(store, "abc", "bug")
        add_tag(store, "abc", "bug")
        assert entry.tags.count("bug") == 1

    def test_add_tag_returns_false_for_missing_entry(self):
        store = _make_store()
        assert add_tag(store, "missing", "tag") is False

    def test_add_empty_tag_raises(self):
        entry = _make_entry("abc")
        store = _make_store(entry)
        with pytest.raises(ValueError):
            add_tag(store, "abc", "   ")


class TestRemoveTag:
    def test_remove_existing_tag(self):
        entry = _make_entry("abc")
        entry.tags = ["bug", "important"]
        store = _make_store(entry)
        result = remove_tag(store, "abc", "bug")
        assert result is True
        assert "bug" not in entry.tags
        assert "important" in entry.tags

    def test_remove_nonexistent_tag_does_not_raise(self):
        entry = _make_entry("abc")
        store = _make_store(entry)
        result = remove_tag(store, "abc", "nonexistent")
        assert result is True

    def test_remove_tag_returns_false_for_missing_entry(self):
        store = _make_store()
        assert remove_tag(store, "missing", "tag") is False


class TestGetTags:
    def test_returns_tags_for_entry(self):
        entry = _make_entry("abc")
        entry.tags = ["x", "y"]
        store = _make_store(entry)
        assert get_tags(store, "abc") == ["x", "y"]

    def test_returns_none_for_missing_entry(self):
        store = _make_store()
        assert get_tags(store, "missing") is None


class TestFilterByTag:
    def test_returns_matching_entries(self):
        e1 = _make_entry("1")
        e1.tags = ["bug"]
        e2 = _make_entry("2")
        e2.tags = ["feature"]
        e3 = _make_entry("3")
        e3.tags = ["bug", "critical"]
        store = _make_store(e1, e2, e3)
        result = filter_by_tag(store, "bug")
        assert len(result) == 2
        assert e1 in result
        assert e3 in result

    def test_returns_empty_when_no_match(self):
        entry = _make_entry("1")
        store = _make_store(entry)
        assert filter_by_tag(store, "nope") == []


class TestListAllTags:
    def test_returns_sorted_unique_tags(self):
        e1 = _make_entry("1")
        e1.tags = ["bug", "urgent"]
        e2 = _make_entry("2")
        e2.tags = ["feature", "bug"]
        store = _make_store(e1, e2)
        assert list_all_tags(store) == ["bug", "feature", "urgent"]

    def test_empty_store_returns_empty(self):
        store = _make_store()
        assert list_all_tags(store) == []
