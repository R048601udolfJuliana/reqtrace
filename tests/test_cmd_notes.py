"""Tests for reqtrace.cmd_notes module."""

import argparse
from io import StringIO
from unittest.mock import patch

from reqtrace.models import HttpRequest, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.notes import add_note
from reqtrace.cmd_notes import cmd_notes


def _make_entry(entry_id="id1"):
    req = HttpRequest(method="POST", url="http://api.test/v1", headers={}, body=None)
    return RequestLogEntry(id=entry_id, timestamp="2024-06-01T12:00:00", request=req)


def _make_store(*entries):
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


def _args(**kwargs):
    defaults = {"notes_action": "show", "id": "id1", "text": ""}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdNotes:
    def test_add_note_prints_confirmation(self, capsys):
        store = _make_store(_make_entry())
        cmd_notes(_args(notes_action="add", text="check this"), store)
        out = capsys.readouterr().out
        assert "Note added" in out

    def test_add_note_missing_entry_prints_error(self, capsys):
        store = LogStore()
        cmd_notes(_args(notes_action="add", id="nope", text="hi"), store)
        out = capsys.readouterr().out
        assert "Error" in out

    def test_add_empty_note_prints_error(self, capsys):
        store = _make_store(_make_entry())
        cmd_notes(_args(notes_action="add", text="  "), store)
        out = capsys.readouterr().out
        assert "Error" in out

    def test_show_no_notes(self, capsys):
        store = _make_store(_make_entry())
        cmd_notes(_args(notes_action="show"), store)
        out = capsys.readouterr().out
        assert "No notes" in out

    def test_show_with_notes(self, capsys):
        store = _make_store(_make_entry())
        add_note(store, "id1", "my note")
        cmd_notes(_args(notes_action="show"), store)
        out = capsys.readouterr().out
        assert "my note" in out

    def test_show_missing_entry_prints_error(self, capsys):
        store = LogStore()
        cmd_notes(_args(notes_action="show", id="ghost"), store)
        out = capsys.readouterr().out
        assert "Error" in out

    def test_clear_notes(self, capsys):
        store = _make_store(_make_entry())
        add_note(store, "id1", "temp")
        cmd_notes(_args(notes_action="clear"), store)
        out = capsys.readouterr().out
        assert "cleared" in out

    def test_clear_missing_entry_prints_error(self, capsys):
        store = LogStore()
        cmd_notes(_args(notes_action="clear", id="gone"), store)
        out = capsys.readouterr().out
        assert "Error" in out

    def test_list_no_annotated_entries(self, capsys):
        store = _make_store(_make_entry())
        cmd_notes(_args(notes_action="list"), store)
        out = capsys.readouterr().out
        assert "No entries" in out

    def test_list_shows_annotated_entries(self, capsys):
        store = _make_store(_make_entry("id1"), _make_entry("id2"))
        add_note(store, "id1", "relevant")
        cmd_notes(_args(notes_action="list"), store)
        out = capsys.readouterr().out
        assert "id1" in out
        assert "id2" not in out
