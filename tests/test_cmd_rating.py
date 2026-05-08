"""Tests for reqtrace.cmd_rating."""

from __future__ import annotations

import argparse
from io import StringIO
from unittest.mock import patch

import pytest

from reqtrace.models import HttpRequest, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.cmd_rating import cmd_rating
from reqtrace.rating import set_rating


def _make_entry(entry_id: str = "abc"):
    req = HttpRequest(method="GET", url="http://example.com/api", headers={}, body=None)
    return RequestLogEntry(id=entry_id, timestamp="2024-01-01T00:00:00Z", request=req)


def _make_store(*entries):
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"rating_action": "set", "id": "abc", "stars": 3, "comment": ""}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdRating:
    def test_set_prints_confirmation(self, capsys):
        store = _make_store(_make_entry("abc"))
        cmd_rating(_args(rating_action="set", id="abc", stars=4, comment=""), store)
        out = capsys.readouterr().out
        assert "abc" in out
        assert "★" in out

    def test_set_invalid_stars_prints_error(self, capsys):
        store = _make_store(_make_entry("abc"))
        cmd_rating(_args(rating_action="set", id="abc", stars=9, comment=""), store)
        out = capsys.readouterr().out
        assert "Error" in out

    def test_set_missing_entry_prints_not_found(self, capsys):
        store = LogStore()
        cmd_rating(_args(rating_action="set", id="ghost", stars=3, comment=""), store)
        out = capsys.readouterr().out
        assert "Not found" in out

    def test_get_shows_stars(self, capsys):
        entry = _make_entry("abc")
        store = _make_store(entry)
        set_rating(store, "abc", 5)
        cmd_rating(_args(rating_action="get", id="abc"), store)
        out = capsys.readouterr().out
        assert "★★★★★" in out

    def test_get_unrated_entry(self, capsys):
        store = _make_store(_make_entry("abc"))
        cmd_rating(_args(rating_action="get", id="abc"), store)
        out = capsys.readouterr().out
        assert "no rating" in out

    def test_get_missing_entry(self, capsys):
        store = LogStore()
        cmd_rating(_args(rating_action="get", id="missing"), store)
        out = capsys.readouterr().out
        assert "not found" in out

    def test_clear_prints_confirmation(self, capsys):
        entry = _make_entry("abc")
        store = _make_store(entry)
        set_rating(store, "abc", 2)
        cmd_rating(_args(rating_action="clear", id="abc"), store)
        out = capsys.readouterr().out
        assert "cleared" in out

    def test_list_empty(self, capsys):
        store = LogStore()
        cmd_rating(_args(rating_action="list"), store)
        out = capsys.readouterr().out
        assert "No rated" in out

    def test_list_shows_entries(self, capsys):
        entry = _make_entry("abc")
        store = _make_store(entry)
        set_rating(store, "abc", 3)
        cmd_rating(_args(rating_action="list"), store)
        out = capsys.readouterr().out
        assert "abc" in out
        assert "★" in out

    def test_filter_no_results(self, capsys):
        store = LogStore()
        cmd_rating(_args(rating_action="filter", min_stars=4), store)
        out = capsys.readouterr().out
        assert "No entries" in out

    def test_filter_shows_matching(self, capsys):
        e1, e2 = _make_entry("e1"), _make_entry("e2")
        store = _make_store(e1, e2)
        set_rating(store, "e1", 5)
        set_rating(store, "e2", 2)
        cmd_rating(_args(rating_action="filter", min_stars=4), store)
        out = capsys.readouterr().out
        assert "e1" in out
        assert "e2" not in out
