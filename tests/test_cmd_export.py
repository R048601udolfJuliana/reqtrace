"""Tests for reqtrace.cmd_export."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import pytest

from reqtrace.cmd_export import cmd_export
from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.storage import LogStore


def _make_entry(entry_id: str = "abc123", method: str = "GET") -> RequestLogEntry:
    req = HttpRequest(
        method=method,
        url="http://example.com/api/test",
        headers={"Content-Type": "application/json"},
        body=None,
    )
    resp = HttpResponse(status_code=200, headers={}, body='{"ok": true}')
    return RequestLogEntry(
        id=entry_id,
        timestamp="2024-01-01T12:00:00",
        request=req,
        response=resp,
    )


def _make_store(*entries: RequestLogEntry) -> LogStore:
    store = LogStore()
    for entry in entries:
        store.add(entry)
    return store


def _args(**kwargs) -> Namespace:
    defaults = {"format": "json", "id": None, "output": None}
    defaults.update(kwargs)
    return Namespace(**defaults)


class TestCmdExport:
    def test_export_json_to_stdout(self, capsys):
        store = _make_store(_make_entry("id1"), _make_entry("id2"))
        rc = cmd_export(_args(format="json"), store)
        captured = capsys.readouterr()
        assert rc == 0
        data = json.loads(captured.out)
        assert len(data) == 2

    def test_export_curl_to_stdout(self, capsys):
        store = _make_store(_make_entry("id1"))
        rc = cmd_export(_args(format="curl"), store)
        captured = capsys.readouterr()
        assert rc == 0
        assert "curl" in captured.out

    def test_export_single_entry_by_id(self, capsys):
        store = _make_store(_make_entry("aaa"), _make_entry("bbb"))
        rc = cmd_export(_args(format="json", id="aaa"), store)
        captured = capsys.readouterr()
        assert rc == 0
        data = json.loads(captured.out)
        assert len(data) == 1
        assert data[0]["id"] == "aaa"

    def test_missing_id_returns_error(self, capsys):
        store = _make_store(_make_entry("aaa"))
        rc = cmd_export(_args(id="nonexistent"), store)
        captured = capsys.readouterr()
        assert rc == 1
        assert "nonexistent" in captured.err

    def test_empty_store_returns_zero(self, capsys):
        store = LogStore()
        rc = cmd_export(_args(), store)
        assert rc == 0

    def test_export_json_to_file(self, tmp_path, capsys):
        out_file = tmp_path / "out.json"
        store = _make_store(_make_entry("id1"))
        rc = cmd_export(_args(format="json", output=str(out_file)), store)
        assert rc == 0
        assert out_file.exists()
        data = json.loads(out_file.read_text())
        assert len(data) == 1

    def test_export_curl_to_file(self, tmp_path):
        out_file = tmp_path / "out.sh"
        store = _make_store(_make_entry("id1"))
        rc = cmd_export(_args(format="curl", output=str(out_file)), store)
        assert rc == 0
        content = out_file.read_text()
        assert "curl" in content

    def test_unknown_format_returns_error(self, capsys):
        store = _make_store(_make_entry("id1"))
        rc = cmd_export(_args(format="xml"), store)
        assert rc == 1
        assert "Unknown format" in capsys.readouterr().err
