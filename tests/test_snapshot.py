"""Tests for reqtrace.snapshot."""

from __future__ import annotations

import json
import pytest

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.snapshot import (
    SnapshotError,
    load_snapshot,
    save_snapshot,
    snapshot_from_json,
    snapshot_to_json,
)
from reqtrace.storage import LogStore


def _make_entry(method="GET", url="http://example.com/api", status=200):
    req = HttpRequest(method=method, url=url, headers={"Accept": "application/json"}, body=None)
    resp = HttpResponse(status_code=status, headers={"Content-Type": "application/json"}, body='{"ok":true}')
    return RequestLogEntry(request=req, response=resp)


def _make_store(*entries):
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


class TestSaveSnapshot:
    def test_name_is_preserved(self):
        store = _make_store(_make_entry())
        snap = save_snapshot(store, "my-snap")
        assert snap["name"] == "my-snap"

    def test_entry_count_matches(self):
        store = _make_store(_make_entry(), _make_entry(method="POST"))
        snap = save_snapshot(store, "s")
        assert len(snap["entries"]) == 2

    def test_empty_store_gives_empty_entries(self):
        store = LogStore()
        snap = save_snapshot(store, "empty")
        assert snap["entries"] == []

    def test_entry_contains_request_fields(self):
        store = _make_store(_make_entry(method="DELETE", url="http://x.com/res"))
        snap = save_snapshot(store, "s")
        req = snap["entries"][0]["request"]
        assert req["method"] == "DELETE"
        assert req["url"] == "http://x.com/res"


class TestLoadSnapshot:
    def test_returns_count_of_loaded_entries(self):
        store = _make_store(_make_entry(), _make_entry())
        snap = save_snapshot(store, "s")
        new_store = LogStore()
        count = load_snapshot(new_store, snap)
        assert count == 2

    def test_entries_are_queryable_after_load(self):
        store = _make_store(_make_entry(url="http://example.com/loaded"))
        snap = save_snapshot(store, "s")
        new_store = LogStore()
        load_snapshot(new_store, snap)
        entries = new_store.all()
        assert any(e.request.url == "http://example.com/loaded" for e in entries)

    def test_ids_are_preserved(self):
        entry = _make_entry()
        store = _make_store(entry)
        snap = save_snapshot(store, "s")
        new_store = LogStore()
        load_snapshot(new_store, snap)
        assert new_store.get_by_id(entry.id) is not None

    def test_missing_entries_key_raises(self):
        with pytest.raises(SnapshotError, match="missing 'entries'"):
            load_snapshot(LogStore(), {"name": "bad"})


class TestJsonRoundtrip:
    def test_serialise_deserialise(self):
        store = _make_store(_make_entry())
        snap = save_snapshot(store, "rt")
        text = snapshot_to_json(snap)
        restored = snapshot_from_json(text)
        assert restored["name"] == "rt"
        assert len(restored["entries"]) == 1

    def test_invalid_json_raises_snapshot_error(self):
        with pytest.raises(SnapshotError, match="Invalid JSON"):
            snapshot_from_json("not json at all")

    def test_output_is_valid_json(self):
        store = _make_store(_make_entry())
        text = snapshot_to_json(save_snapshot(store, "x"))
        parsed = json.loads(text)
        assert "entries" in parsed
