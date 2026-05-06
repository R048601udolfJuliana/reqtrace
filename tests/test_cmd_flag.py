"""Tests for reqtrace.cmd_flag."""
from __future__ import annotations

import argparse
from io import StringIO
from unittest.mock import patch

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.flag import flag_entry
from reqtrace.cmd_flag import cmd_flag


def _make_entry(entry_id: str = "abc123") -> RequestLogEntry:
    req = HttpRequest(method="POST", url="http://api.test/data", headers={}, body="{}")
    resp = HttpResponse(status_code=201, headers={}, body="created")
    return RequestLogEntry(id=entry_id, request=req, response=resp, timestamp="2024-06-01T10:00:00")


def _make_store(*ids: str) -> LogStore:
    store = LogStore()
    for eid in ids:
        store.add(_make_entry(eid))
    return store


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"flag_action": "add", "id": "abc123", "reason": ""}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdFlag:
    def test_add_prints_confirmation(self, capsys):
        store = _make_store("abc123")
        cmd_flag(_args(flag_action="add", id="abc123"), store)
        out = capsys.readouterr().out
        assert "Flagged entry abc123" in out

    def test_add_with_reason_includes_reason(self, capsys):
        store = _make_store("abc123")
        cmd_flag(_args(flag_action="add", id="abc123", reason="urgent"), store)
        out = capsys.readouterr().out
        assert "urgent" in out

    def test_add_missing_entry_prints_error(self, capsys):
        store = LogStore()
        cmd_flag(_args(flag_action="add", id="nope"), store)
        out = capsys.readouterr().out
        assert "nope" in out

    def test_remove_prints_confirmation(self, capsys):
        store = _make_store("abc123")
        flag_entry(store, "abc123")
        cmd_flag(_args(flag_action="remove", id="abc123"), store)
        out = capsys.readouterr().out
        assert "Unflagged entry abc123" in out

    def test_remove_missing_entry_prints_error(self, capsys):
        store = LogStore()
        cmd_flag(_args(flag_action="remove", id="ghost"), store)
        out = capsys.readouterr().out
        assert "ghost" in out

    def test_list_empty_store(self, capsys):
        store = LogStore()
        cmd_flag(_args(flag_action="list"), store)
        out = capsys.readouterr().out
        assert "No flagged entries" in out

    def test_list_shows_flagged_entries(self, capsys):
        store = _make_store("e1", "e2")
        flag_entry(store, "e1", reason="check this")
        cmd_flag(_args(flag_action="list"), store)
        out = capsys.readouterr().out
        assert "e1" in out
        assert "check this" in out
        assert "e2" not in out
