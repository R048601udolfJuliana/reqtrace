"""Tests for reqtrace.cmd_pin module."""

from __future__ import annotations

import argparse
from io import StringIO
from unittest.mock import patch

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.cmd_pin import cmd_pin, add_pin_subcommand
from reqtrace.pin import pin_entry


def _make_entry(entry_id="abc123", method="GET", url="http://api.test/v1", status=200):
    req = HttpRequest(method=method, url=url, headers={}, body=None)
    resp = HttpResponse(status_code=status, headers={}, body=None)
    entry = RequestLogEntry(request=req, response=resp)
    entry.id = entry_id
    return entry


def _make_store(*entries):
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


def _args(**kwargs):
    base = {"pin_action": "list"}
    base.update(kwargs)
    return argparse.Namespace(**base)


class TestCmdPin:
    def test_pin_add_prints_confirmation(self, capsys):
        entry = _make_entry()
        store = _make_store(entry)
        cmd_pin(_args(pin_action="add", id=entry.id), store)
        out = capsys.readouterr().out
        assert "Pinned" in out
        assert entry.id in out

    def test_pin_add_missing_id_prints_not_found(self, capsys):
        store = _make_store()
        cmd_pin(_args(pin_action="add", id="nope"), store)
        out = capsys.readouterr().out
        assert "not found" in out.lower()

    def test_pin_remove_prints_confirmation(self, capsys):
        entry = _make_entry()
        store = _make_store(entry)
        pin_entry(store, entry.id)
        cmd_pin(_args(pin_action="remove", id=entry.id), store)
        out = capsys.readouterr().out
        assert "Unpinned" in out

    def test_pin_remove_missing_id_prints_not_found(self, capsys):
        store = _make_store()
        cmd_pin(_args(pin_action="remove", id="ghost"), store)
        out = capsys.readouterr().out
        assert "not found" in out.lower()

    def test_list_empty_prints_message(self, capsys):
        store = _make_store(_make_entry())
        cmd_pin(_args(pin_action="list"), store)
        out = capsys.readouterr().out
        assert "No pinned" in out

    def test_list_shows_pinned_entries(self, capsys):
        entry = _make_entry(entry_id="deadbeef")
        store = _make_store(entry)
        pin_entry(store, entry.id)
        cmd_pin(_args(pin_action="list"), store)
        out = capsys.readouterr().out
        assert "deadbeef"[:8] in out
        assert "http://api.test/v1" in out

    def test_add_pin_subcommand_registers_parser(self):
        root = argparse.ArgumentParser()
        sub = root.add_subparsers(dest="command")
        add_pin_subcommand(sub)
        args = root.parse_args(["pin", "list"])
        assert args.pin_action == "list"
