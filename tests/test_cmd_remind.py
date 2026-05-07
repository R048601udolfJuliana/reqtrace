"""Tests for reqtrace.cmd_remind."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
from io import StringIO
from unittest.mock import patch

from reqtrace.models import HttpRequest, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.cmd_remind import cmd_remind
from reqtrace.remind import set_reminder


def _make_entry(entry_id: str = "id1") -> RequestLogEntry:
    req = HttpRequest(method="POST", url="http://api.local/test", headers={}, body=None)
    return RequestLogEntry(
        id=entry_id,
        timestamp="2024-06-01T12:00:00+00:00",
        request=req,
        response=None,
        metadata={},
    )


def _make_store(*entries) -> LogStore:
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"remind_action": "set", "id": "id1", "minutes": 10, "note": ""}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdRemind:
    def test_set_prints_confirmation(self, capsys):
        store = _make_store(_make_entry())
        cmd_remind(_args(remind_action="set", minutes=20), store)
        out = capsys.readouterr().out
        assert "Reminder set" in out
        assert "id1" in out

    def test_set_prints_note_when_provided(self, capsys):
        store = _make_store(_make_entry())
        cmd_remind(_args(remind_action="set", minutes=5, note="follow up"), store)
        out = capsys.readouterr().out
        assert "follow up" in out

    def test_set_missing_entry_prints_error(self, capsys):
        store = _make_store()
        cmd_remind(_args(remind_action="set", id="ghost", minutes=5), store)
        out = capsys.readouterr().out
        assert "Error" in out

    def test_set_zero_minutes_prints_error(self, capsys):
        store = _make_store(_make_entry())
        cmd_remind(_args(remind_action="set", minutes=0), store)
        out = capsys.readouterr().out
        assert "Error" in out

    def test_clear_prints_confirmation(self, capsys):
        store = _make_store(_make_entry())
        set_reminder(store, "id1", 30)
        cmd_remind(_args(remind_action="clear"), store)
        out = capsys.readouterr().out
        assert "cleared" in out

    def test_show_no_reminder(self, capsys):
        store = _make_store(_make_entry())
        cmd_remind(_args(remind_action="show"), store)
        out = capsys.readouterr().out
        assert "No reminder" in out

    def test_show_with_reminder(self, capsys):
        store = _make_store(_make_entry())
        set_reminder(store, "id1", 60, note="revisit")
        cmd_remind(_args(remind_action="show"), store)
        out = capsys.readouterr().out
        assert "Reminder:" in out
        assert "revisit" in out

    def test_due_prints_due_entries(self, capsys):
        e = _make_entry()
        past = datetime.now(timezone.utc) - timedelta(minutes=1)
        e.metadata["remind_at"] = past.isoformat()
        store = _make_store(e)
        cmd_remind(_args(remind_action="due"), store)
        out = capsys.readouterr().out
        assert "id1" in out

    def test_due_empty_message(self, capsys):
        store = _make_store(_make_entry())
        cmd_remind(_args(remind_action="due"), store)
        out = capsys.readouterr().out
        assert "No reminders" in out
