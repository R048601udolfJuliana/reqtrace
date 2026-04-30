"""Tests for reqtrace.cmd_compare."""

from __future__ import annotations

import argparse
from io import StringIO
from unittest.mock import patch

from reqtrace.models import HttpRequest, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.cmd_compare import cmd_compare


def _make_entry(
    entry_id: str,
    method: str = "GET",
    url: str = "http://example.com/api",
) -> RequestLogEntry:
    req = HttpRequest(method=method, url=url, headers={}, body=None)
    return RequestLogEntry(id=entry_id, timestamp="2024-01-01T00:00:00", request=req)


def _make_store(*entries: RequestLogEntry) -> LogStore:
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


def _args(id_a: str, id_b: str) -> argparse.Namespace:
    return argparse.Namespace(id_a=id_a, id_b=id_b)


class TestCmdCompare:
    def test_prints_similarity_summary(self, capsys):
        a = _make_entry("aaa")
        b = _make_entry("bbb")
        store = _make_store(a, b)
        cmd_compare(_args("aaa", "bbb"), store)
        out = capsys.readouterr().out
        assert "Similarity" in out

    def test_missing_first_entry_prints_error(self, capsys):
        b = _make_entry("bbb")
        store = _make_store(b)
        cmd_compare(_args("missing", "bbb"), store)
        out = capsys.readouterr().out
        assert "not found" in out.lower()

    def test_missing_second_entry_prints_error(self, capsys):
        a = _make_entry("aaa")
        store = _make_store(a)
        cmd_compare(_args("aaa", "missing"), store)
        out = capsys.readouterr().out
        assert "not found" in out.lower()

    def test_identical_entries_shows_100_percent(self, capsys):
        a = _make_entry("aaa")
        b = _make_entry("bbb")
        store = _make_store(a, b)
        cmd_compare(_args("aaa", "bbb"), store)
        out = capsys.readouterr().out
        assert "100%" in out

    def test_different_methods_reflected_in_output(self, capsys):
        a = _make_entry("aaa", method="GET")
        b = _make_entry("bbb", method="DELETE")
        store = _make_store(a, b)
        cmd_compare(_args("aaa", "bbb"), store)
        out = capsys.readouterr().out
        assert "GET" in out
        assert "DELETE" in out
