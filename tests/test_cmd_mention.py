"""Tests for reqtrace.cmd_mention."""

import argparse
from io import StringIO
from unittest.mock import patch

from reqtrace.models import HttpRequest, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.mention import add_mention
from reqtrace.cmd_mention import cmd_mention


def _make_entry(entry_id: str = "abc"):
    req = HttpRequest(method="GET", url="http://example.com/api", headers={}, body=None)
    return RequestLogEntry(id=entry_id, timestamp="2024-01-01T00:00:00", request=req)


def _make_store(*entries):
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


def _args(**kwargs):
    base = {"mention_action": "add", "id": "abc", "name": "alice"}
    base.update(kwargs)
    return argparse.Namespace(**base)


class TestCmdMention:
    def test_add_prints_confirmation(self, capsys):
        store = _make_store(_make_entry("abc"))
        cmd_mention(_args(mention_action="add", id="abc", name="alice"), store)
        out = capsys.readouterr().out
        assert "alice" in out
        assert "abc" in out

    def test_add_missing_entry_prints_error(self, capsys):
        store = _make_store()
        cmd_mention(_args(mention_action="add", id="nope", name="alice"), store)
        out = capsys.readouterr().out
        assert "nope" in out

    def test_remove_prints_confirmation(self, capsys):
        store = _make_store(_make_entry("abc"))
        add_mention(store, "abc", "alice")
        cmd_mention(_args(mention_action="remove", id="abc", name="alice"), store)
        out = capsys.readouterr().out
        assert "alice" in out

    def test_list_shows_mentions(self, capsys):
        store = _make_store(_make_entry("abc"))
        add_mention(store, "abc", "bob")
        cmd_mention(_args(mention_action="list", id="abc"), store)
        out = capsys.readouterr().out
        assert "bob" in out

    def test_list_empty_prints_message(self, capsys):
        store = _make_store(_make_entry("abc"))
        cmd_mention(_args(mention_action="list", id="abc"), store)
        out = capsys.readouterr().out
        assert "No mentions" in out

    def test_list_missing_entry_prints_error(self, capsys):
        store = _make_store()
        cmd_mention(_args(mention_action="list", id="missing"), store)
        out = capsys.readouterr().out
        assert "missing" in out

    def test_search_returns_matches(self, capsys):
        store = _make_store(_make_entry("abc"))
        add_mention(store, "abc", "carol")
        cmd_mention(_args(mention_action="search", name="carol"), store)
        out = capsys.readouterr().out
        assert "abc" in out

    def test_search_no_match_prints_message(self, capsys):
        store = _make_store(_make_entry("abc"))
        cmd_mention(_args(mention_action="search", name="nobody"), store)
        out = capsys.readouterr().out
        assert "nobody" in out

    def test_all_lists_every_mention(self, capsys):
        store = _make_store(_make_entry("1"), _make_entry("2"))
        add_mention(store, "1", "dave")
        add_mention(store, "2", "eve")
        cmd_mention(_args(mention_action="all"), store)
        out = capsys.readouterr().out
        assert "dave" in out
        assert "eve" in out
