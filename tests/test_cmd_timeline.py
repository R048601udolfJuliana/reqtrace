"""Tests for reqtrace.cmd_timeline."""

from __future__ import annotations

import io
import argparse

import pytest

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.cmd_timeline import add_timeline_subcommand, cmd_timeline


def _make_entry(entry_id: str, timestamp: str) -> RequestLogEntry:
    req = HttpRequest(method="GET", url="http://example.com/test", headers={}, body=None)
    resp = HttpResponse(status_code=200, headers={}, body=None)
    return RequestLogEntry(id=entry_id, timestamp=timestamp, request=req, response=resp)


def _make_store(*entries: RequestLogEntry) -> LogStore:
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


class TestCmdTimeline:
    def _args(self, descending: bool = False) -> argparse.Namespace:
        return argparse.Namespace(descending=descending)

    def test_empty_store_prints_no_entries(self):
        store = _make_store()
        out = io.StringIO()
        cmd_timeline(self._args(), store, out=out)
        assert "No entries." in out.getvalue()

    def test_prints_bucket_header(self):
        e = _make_entry("abc", "2024-06-01T12:05:00Z")
        store = _make_store(e)
        out = io.StringIO()
        cmd_timeline(self._args(), store, out=out)
        assert "2024-06-01T12:05" in out.getvalue()

    def test_descending_flag_passed(self):
        e1 = _make_entry("e1", "2024-06-01T10:00:00Z")
        e2 = _make_entry("e2", "2024-06-01T11:00:00Z")
        store = _make_store(e1, e2)
        out = io.StringIO()
        cmd_timeline(self._args(descending=True), store, out=out)
        text = out.getvalue()
        assert text.index("11:00") < text.index("10:00")

    def test_add_timeline_subcommand_registers(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        add_timeline_subcommand(subparsers)
        args = parser.parse_args(["timeline"])
        assert hasattr(args, "func")

    def test_add_timeline_subcommand_desc_flag(self):
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        add_timeline_subcommand(subparsers)
        args = parser.parse_args(["timeline", "--desc"])
        assert args.descending is True
