"""Tests for reqtrace.bookmark and reqtrace.cmd_bookmark."""

from __future__ import annotations

import argparse
import pytest

from reqtrace.models import HttpRequest, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.bookmark import (
    bookmark_entry,
    unbookmark_entry,
    is_bookmarked,
    list_bookmarks,
    _BOOKMARK_TAG,
)
from reqtrace.cmd_bookmark import cmd_bookmark


def _make_entry(entry_id: str = "abc123", method: str = "GET") -> RequestLogEntry:
    req = HttpRequest(method=method, url="http://example.com/api", headers={}, body=None)
    return RequestLogEntry(id=entry_id, request=req, response=None, timestamp="2024-01-01T00:00:00")


def _make_store(*entries: RequestLogEntry) -> LogStore:
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


class TestBookmarkEntry:
    def test_bookmark_adds_tag(self):
        store = _make_store(_make_entry("e1"))
        entry = bookmark_entry(store, "e1")
        assert _BOOKMARK_TAG in entry.tags

    def test_bookmark_idempotent(self):
        store = _make_store(_make_entry("e1"))
        bookmark_entry(store, "e1")
        entry = bookmark_entry(store, "e1")
        assert entry.tags.count(_BOOKMARK_TAG) == 1

    def test_bookmark_raises_for_unknown_id(self):
        store = _make_store()
        with pytest.raises(KeyError):
            bookmark_entry(store, "missing")


class TestUnbookmarkEntry:
    def test_removes_bookmark_tag(self):
        store = _make_store(_make_entry("e1"))
        bookmark_entry(store, "e1")
        entry = unbookmark_entry(store, "e1")
        assert _BOOKMARK_TAG not in (entry.tags or [])

    def test_unbookmark_non_bookmarked_is_safe(self):
        store = _make_store(_make_entry("e1"))
        entry = unbookmark_entry(store, "e1")
        assert _BOOKMARK_TAG not in (entry.tags or [])

    def test_unbookmark_raises_for_unknown_id(self):
        store = _make_store()
        with pytest.raises(KeyError):
            unbookmark_entry(store, "missing")


class TestListBookmarks:
    def test_empty_store_returns_empty(self):
        assert list_bookmarks(_make_store()) == []

    def test_returns_only_bookmarked(self):
        e1 = _make_entry("e1")
        e2 = _make_entry("e2")
        store = _make_store(e1, e2)
        bookmark_entry(store, "e1")
        result = list_bookmarks(store)
        assert len(result) == 1
        assert result[0].id == "e1"


class TestCmdBookmark:
    def _args(self, bookmark_cmd: str, entry_id: str | None = None) -> argparse.Namespace:
        ns = argparse.Namespace(bookmark_cmd=bookmark_cmd)
        if entry_id is not None:
            ns.id = entry_id
        return ns

    def test_cmd_add_prints_confirmation(self, capsys):
        store = _make_store(_make_entry("e1"))
        cmd_bookmark(self._args("add", "e1"), store)
        assert "Bookmarked entry e1" in capsys.readouterr().out

    def test_cmd_add_unknown_id_prints_error(self, capsys):
        store = _make_store()
        cmd_bookmark(self._args("add", "nope"), store)
        assert "Error" in capsys.readouterr().out

    def test_cmd_remove_prints_confirmation(self, capsys):
        store = _make_store(_make_entry("e1"))
        bookmark_entry(store, "e1")
        cmd_bookmark(self._args("remove", "e1"), store)
        assert "Removed bookmark" in capsys.readouterr().out

    def test_cmd_list_empty(self, capsys):
        store = _make_store()
        cmd_bookmark(self._args("list"), store)
        assert "No bookmarked" in capsys.readouterr().out

    def test_cmd_list_shows_bookmarked(self, capsys):
        store = _make_store(_make_entry("e1"))
        bookmark_entry(store, "e1")
        cmd_bookmark(self._args("list"), store)
        assert "e1" in capsys.readouterr().out
