"""Tests for reqtrace.mention."""

import pytest

from reqtrace.models import HttpRequest, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.mention import (
    add_mention,
    remove_mention,
    get_mentions,
    list_entries_with_mention,
    list_all_mentions,
)


def _make_entry(entry_id: str = "abc", method: str = "GET", url: str = "http://example.com"):
    req = HttpRequest(method=method, url=url, headers={}, body=None)
    return RequestLogEntry(id=entry_id, timestamp="2024-01-01T00:00:00", request=req)


def _make_store(*entries):
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


class TestAddMention:
    def test_add_mention_normalises_at_prefix(self):
        store = _make_store(_make_entry("1"))
        add_mention(store, "1", "@Alice")
        entry = store.get_by_id("1")
        assert "alice" in get_mentions(entry)

    def test_add_mention_idempotent(self):
        store = _make_store(_make_entry("1"))
        add_mention(store, "1", "bob")
        add_mention(store, "1", "bob")
        assert get_mentions(store.get_by_id("1")).count("bob") == 1

    def test_add_multiple_mentions(self):
        store = _make_store(_make_entry("1"))
        add_mention(store, "1", "alice")
        add_mention(store, "1", "bob")
        mentions = get_mentions(store.get_by_id("1"))
        assert "alice" in mentions
        assert "bob" in mentions

    def test_add_raises_for_missing_entry(self):
        store = _make_store()
        with pytest.raises(KeyError):
            add_mention(store, "missing", "alice")

    def test_empty_mention_raises(self):
        store = _make_store(_make_entry("1"))
        with pytest.raises(ValueError):
            add_mention(store, "1", "@")


class TestRemoveMention:
    def test_remove_existing_mention(self):
        store = _make_store(_make_entry("1"))
        add_mention(store, "1", "alice")
        remove_mention(store, "1", "alice")
        assert get_mentions(store.get_by_id("1")) == []

    def test_remove_nonexistent_mention_is_safe(self):
        store = _make_store(_make_entry("1"))
        remove_mention(store, "1", "ghost")  # should not raise

    def test_remove_raises_for_missing_entry(self):
        store = _make_store()
        with pytest.raises(KeyError):
            remove_mention(store, "missing", "alice")


class TestListEntriesWithMention:
    def test_returns_matching_entries(self):
        e1 = _make_entry("1")
        e2 = _make_entry("2")
        store = _make_store(e1, e2)
        add_mention(store, "1", "alice")
        results = list_entries_with_mention(store, "alice")
        assert len(results) == 1
        assert results[0].id == "1"

    def test_returns_empty_when_no_match(self):
        store = _make_store(_make_entry("1"))
        assert list_entries_with_mention(store, "nobody") == []


class TestListAllMentions:
    def test_returns_sorted_unique_mentions(self):
        e1 = _make_entry("1")
        e2 = _make_entry("2")
        store = _make_store(e1, e2)
        add_mention(store, "1", "charlie")
        add_mention(store, "2", "alice")
        add_mention(store, "1", "alice")
        assert list_all_mentions(store) == ["alice", "charlie"]

    def test_empty_store_returns_empty(self):
        store = _make_store()
        assert list_all_mentions(store) == []
