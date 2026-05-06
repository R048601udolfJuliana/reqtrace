"""Tests for reqtrace.cmd_assert."""

import argparse
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from reqtrace.cmd_assert import cmd_assert
from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.storage import LogStore


def _make_entry(status: int = 200, body: str = "ok") -> RequestLogEntry:
    req = HttpRequest(method="GET", url="http://example.com/", headers={}, body=None)
    resp = HttpResponse(status_code=status, headers={}, body=body)
    return RequestLogEntry(request=req, response=resp, timestamp="2024-01-01T00:00:00")


def _make_store(*entries) -> LogStore:
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


def _args(**kwargs) -> argparse.Namespace:
    defaults = dict(id=None, status=None, body_contains=None, header=[], max_latency_ms=None)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdAssert:
    def test_pass_prints_pass(self, capsys):
        store = _make_store(_make_entry(status=200))
        cmd_assert(_args(status=200), store)
        out = capsys.readouterr().out
        assert "PASS" in out

    def test_fail_exits_with_2(self, capsys):
        store = _make_store(_make_entry(status=404))
        with pytest.raises(SystemExit) as exc:
            cmd_assert(_args(status=200), store)
        assert exc.value.code == 2

    def test_missing_id_exits_1(self, capsys):
        store = _make_store()
        with pytest.raises(SystemExit) as exc:
            cmd_assert(_args(id="nonexistent"), store)
        assert exc.value.code == 1

    def test_single_id_asserted(self, capsys):
        entry = _make_entry(status=201)
        store = _make_store(entry)
        cmd_assert(_args(id=entry.id, status=201), store)
        out = capsys.readouterr().out
        assert "PASS" in out

    def test_invalid_header_format_exits_1(self, capsys):
        store = _make_store(_make_entry())
        with pytest.raises(SystemExit) as exc:
            cmd_assert(_args(header=["BadHeaderNoColon"]), store)
        assert exc.value.code == 1

    def test_empty_store_prints_message(self, capsys):
        store = _make_store()
        cmd_assert(_args(), store)
        out = capsys.readouterr().out
        assert "No entries" in out

    def test_body_contains_fail_exits_2(self, capsys):
        store = _make_store(_make_entry(body="hello"))
        with pytest.raises(SystemExit) as exc:
            cmd_assert(_args(body_contains="missing"), store)
        assert exc.value.code == 2
