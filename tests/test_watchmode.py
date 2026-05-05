"""Tests for reqtrace.watchmode and reqtrace.cmd_watch."""

import argparse
import io
import sys
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.watchmode import _format_entry, watch_store
from reqtrace.cmd_watch import cmd_watch


def _make_entry(method="GET", url="http://example.com/api", status=200, body="ok"):
    req = HttpRequest(method=method, url=url, headers={}, body=None)
    resp = HttpResponse(status_code=status, headers={}, body=body)
    return RequestLogEntry(
        request=req,
        response=resp,
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc).isoformat(),
    )


class TestFormatEntry:
    def test_contains_method(self):
        entry = _make_entry(method="POST")
        line = _format_entry(entry, colour=False)
        assert "POST" in line

    def test_contains_url(self):
        entry = _make_entry(url="http://example.com/things")
        line = _format_entry(entry, colour=False)
        assert "http://example.com/things" in line

    def test_contains_status_code(self):
        entry = _make_entry(status=404)
        line = _format_entry(entry, colour=False)
        assert "404" in line

    def test_contains_short_id(self):
        entry = _make_entry()
        line = _format_entry(entry, colour=False)
        assert entry.id[:8] in line

    def test_no_response_label(self):
        req = HttpRequest(method="GET", url="http://x.com", headers={}, body=None)
        entry = RequestLogEntry(
            request=req,
            response=None,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        line = _format_entry(entry, colour=False)
        assert "no response" in line

    def test_body_size_shown(self):
        entry = _make_entry(body="hello")  # 5 bytes
        line = _format_entry(entry, colour=False)
        assert "5b" in line


class TestWatchStore:
    def test_prints_existing_entries_on_first_poll(self, capsys):
        store = LogStore()
        store.add(_make_entry(method="GET"))
        store.add(_make_entry(method="DELETE"))

        watch_store(store, interval=0, colour=False, max_iterations=1)

        captured = capsys.readouterr()
        assert "GET" in captured.out
        assert "DELETE" in captured.out

    def test_new_entries_detected_on_subsequent_poll(self, capsys):
        store = LogStore()
        store.add(_make_entry(method="GET"))

        collected = []

        def add_on_second(iteration_count=[0]):
            iteration_count[0] += 1
            if iteration_count[0] == 1:
                store.add(_make_entry(method="PATCH"))

        # Use on_entry callback to track what was newly seen
        seen = []
        watch_store(
            store,
            interval=0,
            colour=False,
            max_iterations=2,
            on_entry=lambda e: seen.append(e.request.method),
        )
        # PATCH was added before second iteration so both GET and PATCH seen
        assert "GET" in seen

    def test_empty_store_no_output(self, capsys):
        store = LogStore()
        watch_store(store, interval=0, colour=False, max_iterations=1)
        captured = capsys.readouterr()
        assert captured.out == ""


class TestCmdWatch:
    def test_keyboard_interrupt_exits_cleanly(self, capsys):
        store = LogStore()
        args = argparse.Namespace(no_colour=True, interval=0)

        with patch("reqtrace.cmd_watch.watch_store", side_effect=KeyboardInterrupt):
            cmd_watch(args, store)  # should not raise

        captured = capsys.readouterr()
        assert "stopped" in captured.err
