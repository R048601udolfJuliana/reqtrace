"""Tests for reqtrace.archive and reqtrace.cmd_archive."""

from __future__ import annotations

import argparse
import unittest
from unittest.mock import patch

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.archive import (
    archive_entry,
    unarchive_entry,
    is_archived,
    list_archived,
    list_active,
    purge_archived,
)
from reqtrace.cmd_archive import cmd_archive


def _make_entry(entry_id="abc123", method="GET", url="http://example.com/"):
    req = HttpRequest(method=method, url=url, headers={}, body=None)
    return RequestLogEntry(id=entry_id, request=req, response=None, timestamp="2024-01-01T00:00:00")


def _make_store(*entries):
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


class TestArchiveEntry(unittest.TestCase):
    def test_archive_sets_metadata(self):
        store = _make_store(_make_entry("id1"))
        result = archive_entry(store, "id1")
        self.assertTrue(result)
        entry = store.get_by_id("id1")
        self.assertTrue(is_archived(entry))

    def test_archive_adds_archived_tag(self):
        store = _make_store(_make_entry("id1"))
        archive_entry(store, "id1")
        entry = store.get_by_id("id1")
        self.assertIn("archived", entry.metadata.get("tags", []))

    def test_archive_returns_false_for_missing_id(self):
        store = _make_store()
        self.assertFalse(archive_entry(store, "missing"))

    def test_archive_idempotent(self):
        store = _make_store(_make_entry("id1"))
        archive_entry(store, "id1")
        archive_entry(store, "id1")
        entry = store.get_by_id("id1")
        self.assertEqual(entry.metadata["tags"].count("archived"), 1)


class TestUnarchiveEntry(unittest.TestCase):
    def test_unarchive_removes_metadata(self):
        store = _make_store(_make_entry("id1"))
        archive_entry(store, "id1")
        result = unarchive_entry(store, "id1")
        self.assertTrue(result)
        entry = store.get_by_id("id1")
        self.assertFalse(is_archived(entry))

    def test_unarchive_removes_tag(self):
        store = _make_store(_make_entry("id1"))
        archive_entry(store, "id1")
        unarchive_entry(store, "id1")
        entry = store.get_by_id("id1")
        self.assertNotIn("archived", entry.metadata.get("tags", []))

    def test_unarchive_returns_false_for_missing_id(self):
        store = _make_store()
        self.assertFalse(unarchive_entry(store, "nope"))


class TestListHelpers(unittest.TestCase):
    def test_list_archived_returns_only_archived(self):
        e1 = _make_entry("a")
        e2 = _make_entry("b")
        store = _make_store(e1, e2)
        archive_entry(store, "a")
        archived = list_archived(store)
        self.assertEqual([x.id for x in archived], ["a"])

    def test_list_active_excludes_archived(self):
        e1 = _make_entry("a")
        e2 = _make_entry("b")
        store = _make_store(e1, e2)
        archive_entry(store, "a")
        active = list_active(store)
        self.assertEqual([x.id for x in active], ["b"])

    def test_purge_removes_archived_entries(self):
        e1 = _make_entry("a")
        e2 = _make_entry("b")
        store = _make_store(e1, e2)
        archive_entry(store, "a")
        count = purge_archived(store)
        self.assertEqual(count, 1)
        self.assertIsNone(store.get_by_id("a"))
        self.assertIsNotNone(store.get_by_id("b"))


class TestCmdArchive(unittest.TestCase):
    def _args(self, action, **kwargs):
        ns = argparse.Namespace(archive_action=action, **kwargs)
        return ns

    def test_add_prints_confirmation(self):
        store = _make_store(_make_entry("id1"))
        args = self._args("add", id="id1")
        with patch("builtins.print") as mock_print:
            cmd_archive(args, store)
        mock_print.assert_called_once_with("Entry id1 archived.")

    def test_add_prints_not_found(self):
        store = _make_store()
        args = self._args("add", id="missing")
        with patch("builtins.print") as mock_print:
            cmd_archive(args, store)
        mock_print.assert_called_once_with("Entry missing not found.")

    def test_remove_prints_confirmation(self):
        store = _make_store(_make_entry("id1"))
        archive_entry(store, "id1")
        args = self._args("remove", id="id1")
        with patch("builtins.print") as mock_print:
            cmd_archive(args, store)
        mock_print.assert_called_once_with("Entry id1 unarchived.")

    def test_list_empty_prints_message(self):
        store = _make_store()
        args = self._args("list", show="archived")
        with patch("builtins.print") as mock_print:
            cmd_archive(args, store)
        mock_print.assert_called_once_with("No entries found.")

    def test_purge_prints_count(self):
        e1 = _make_entry("a")
        store = _make_store(e1)
        archive_entry(store, "a")
        args = self._args("purge")
        with patch("builtins.print") as mock_print:
            cmd_archive(args, store)
        mock_print.assert_called_once_with("Purged 1 archived entry/entries.")


if __name__ == "__main__":
    unittest.main()
