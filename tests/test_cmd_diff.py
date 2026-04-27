"""Tests for the diff CLI command."""

import pytest
from unittest.mock import MagicMock
from reqtrace.cmd_diff import cmd_diff
from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.storage import LogStore


def _make_entry(entry_id: str, method: str = "GET", status: int = 200) -> RequestLogEntry:
    req = HttpRequest(method=method, url="http://example.com/", headers={}, body=None)
    resp = HttpResponse(status_code=status, headers={}, body="{}")
    return RequestLogEntry(id=entry_id, request=req, response=resp)


def _make_store(*entries) -> LogStore:
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


class TestCmdDiff:
    def test_prints_no_differences(self, capsys):
        a = _make_entry("aaa")
        b = _make_entry("bbb")
        store = _make_store(a, b)
        args = MagicMock(id_a="aaa", id_b="bbb")
        cmd_diff(args, store=store)
        captured = capsys.readouterr()
        assert "No differences" in captured.out

    def test_prints_diff_when_methods_differ(self, capsys):
        a = _make_entry("aaa", method="GET")
        b = _make_entry("bbb", method="POST")
        store = _make_store(a, b)
        args = MagicMock(id_a="aaa", id_b="bbb")
        cmd_diff(args, store=store)
        captured = capsys.readouterr()
        assert "method" in captured.out

    def test_missing_left_entry(self, capsys):
        b = _make_entry("bbb")
        store = _make_store(b)
        args = MagicMock(id_a="missing", id_b="bbb")
        cmd_diff(args, store=store)
        captured = capsys.readouterr()
        assert "missing" in captured.out

    def test_missing_right_entry(self, capsys):
        a = _make_entry("aaa")
        store = _make_store(a)
        args = MagicMock(id_a="aaa", id_b="ghost")
        cmd_diff(args, store=store)
        captured = capsys.readouterr()
        assert "ghost" in captured.out

    def test_status_code_diff_shown(self, capsys):
        a = _make_entry("aaa", status=200)
        b = _make_entry("bbb", status=500)
        store = _make_store(a, b)
        args = MagicMock(id_a="aaa", id_b="bbb")
        cmd_diff(args, store=store)
        captured = capsys.readouterr()
        assert "response.status_code" in captured.out
