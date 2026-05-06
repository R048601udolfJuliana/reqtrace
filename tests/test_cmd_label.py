"""Tests for reqtrace.cmd_label"""

from __future__ import annotations

import types
import sys
from io import StringIO

import pytest

from reqtrace.models import HttpRequest, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace import label as label_mod
from reqtrace.cmd_label import cmd_label


def _make_entry(entry_id: str = "abc") -> RequestLogEntry:
    req = HttpRequest(method="GET", url="http://example.com/",
                      headers={}, body=None)
    return RequestLogEntry(id=entry_id, timestamp="2024-01-01T00:00:00",
                           request=req, response=None, metadata={})


def _make_store(*entries) -> LogStore:
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


def _args(**kwargs) -> types.SimpleNamespace:
    defaults = {"label_action": "add", "id": "abc", "label": "test"}
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


class TestCmdLabel:
    def test_add_prints_confirmation(self, capsys):
        store = _make_store(_make_entry("abc"))
        cmd_label(_args(label_action="add", id="abc", label="flow"), store)
        out = capsys.readouterr().out
        assert "flow" in out
        assert "abc" in out

    def test_add_missing_entry_exits(self, capsys):
        store = LogStore()
        with pytest.raises(SystemExit):
            cmd_label(_args(label_action="add", id="nope", label="x"), store)

    def test_remove_prints_confirmation(self, capsys):
        store = _make_store(_make_entry("abc"))
        label_mod.add_label(store, "abc", "remove-me")
        cmd_label(_args(label_action="remove", id="abc", label="remove-me"), store)
        out = capsys.readouterr().out
        assert "remove-me" in out

    def test_remove_missing_entry_exits(self, capsys):
        store = LogStore()
        with pytest.raises(SystemExit):
            cmd_label(_args(label_action="remove", id="nope", label="x"), store)

    def test_list_entry_labels(self, capsys):
        store = _make_store(_make_entry("abc"))
        label_mod.add_label(store, "abc", "visible")
        cmd_label(_args(label_action="list", id="abc"), store)
        out = capsys.readouterr().out
        assert "visible" in out

    def test_list_global_labels(self, capsys):
        store = _make_store(_make_entry("abc"))
        label_mod.add_label(store, "abc", "global-lbl")
        cmd_label(_args(label_action="list", id=None), store)
        out = capsys.readouterr().out
        assert "global-lbl" in out

    def test_list_no_labels_prints_message(self, capsys):
        store = _make_store(_make_entry("abc"))
        cmd_label(_args(label_action="list", id="abc"), store)
        out = capsys.readouterr().out
        assert "No labels" in out

    def test_filter_prints_matching_entries(self, capsys):
        store = _make_store(_make_entry("abc"))
        label_mod.add_label(store, "abc", "target")
        cmd_label(_args(label_action="filter", label="target"), store)
        out = capsys.readouterr().out
        assert "abc" in out

    def test_filter_no_match_prints_message(self, capsys):
        store = _make_store(_make_entry("abc"))
        cmd_label(_args(label_action="filter", label="ghost"), store)
        out = capsys.readouterr().out
        assert "No entries" in out
