"""Tests for reqtrace.cmd_snapshot."""

from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.snapshot import save_snapshot, snapshot_to_json
from reqtrace.storage import LogStore
from reqtrace.cmd_snapshot import cmd_snapshot


def _make_entry(method="GET", url="http://example.com/"):
    req = HttpRequest(method=method, url=url, headers={}, body=None)
    resp = HttpResponse(status_code=200, headers={}, body="ok")
    return RequestLogEntry(request=req, response=resp)


def _make_store(*entries):
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


def _args(**kwargs):
    base = {"snapshot_cmd": "save", "name": "default", "output": None, "input": None}
    base.update(kwargs)
    return types.SimpleNamespace(**base)


class TestCmdSnapshotSave:
    def test_save_prints_json_to_stdout(self, capsys):
        store = _make_store(_make_entry())
        cmd_snapshot(_args(snapshot_cmd="save", output=None), store)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "entries" in data
        assert len(data["entries"]) == 1

    def test_save_writes_file(self, tmp_path):
        store = _make_store(_make_entry(), _make_entry(method="POST"))
        out_file = str(tmp_path / "snap.json")
        cmd_snapshot(_args(snapshot_cmd="save", output=out_file, name="test-snap"), store)
        content = json.loads(Path(out_file).read_text())
        assert content["name"] == "test-snap"
        assert len(content["entries"]) == 2

    def test_save_prints_confirmation_when_file_given(self, tmp_path, capsys):
        store = _make_store(_make_entry())
        out_file = str(tmp_path / "snap.json")
        cmd_snapshot(_args(snapshot_cmd="save", output=out_file, name="s"), store)
        out = capsys.readouterr().out
        assert "saved" in out


class TestCmdSnapshotLoad:
    def test_load_adds_entries_to_store(self, tmp_path):
        entry = _make_entry(url="http://loaded.example.com/")
        original_store = _make_store(entry)
        snap = save_snapshot(original_store, "snap")
        snap_file = tmp_path / "snap.json"
        snap_file.write_text(snapshot_to_json(snap))

        new_store = LogStore()
        cmd_snapshot(_args(snapshot_cmd="load", input=str(snap_file)), new_store)
        assert any(e.request.url == "http://loaded.example.com/" for e in new_store.all())

    def test_load_prints_count(self, tmp_path, capsys):
        store = _make_store(_make_entry(), _make_entry())
        snap_file = tmp_path / "snap.json"
        snap_file.write_text(snapshot_to_json(save_snapshot(store, "s")))
        new_store = LogStore()
        cmd_snapshot(_args(snapshot_cmd="load", input=str(snap_file)), new_store)
        out = capsys.readouterr().out
        assert "2" in out

    def test_load_missing_input_exits(self, capsys):
        with pytest.raises(SystemExit):
            cmd_snapshot(_args(snapshot_cmd="load", input=None), LogStore())

    def test_load_bad_json_exits(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not valid json")
        with pytest.raises(SystemExit):
            cmd_snapshot(_args(snapshot_cmd="load", input=str(bad_file)), LogStore())
