"""Tests for HttpRequest, HttpResponse, RequestLogEntry, and LogStore."""

import json
import tempfile
from pathlib import Path

import pytest

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.storage import LogStore


def make_entry(method="GET", url="http://example.com/api", status=200):
    request = HttpRequest(method=method, url=url, headers={"Accept": "application/json"})
    response = HttpResponse(status_code=status, body=b'{"ok": true}', elapsed_ms=42.5)
    return RequestLogEntry(request=request, response=response)


class TestModels:
    def test_request_to_dict(self):
        req = HttpRequest(method="POST", url="http://api.test/items", body=b"hello")
        d = req.to_dict()
        assert d["method"] == "POST"
        assert d["body"] == "hello"
        assert "request_id" in d
        assert "timestamp" in d

    def test_response_to_dict(self):
        res = HttpResponse(status_code=404, body=b"not found", elapsed_ms=10.0)
        d = res.to_dict()
        assert d["status_code"] == 404
        assert d["body"] == "not found"
        assert d["elapsed_ms"] == 10.0

    def test_log_entry_no_response(self):
        req = HttpRequest(method="DELETE", url="http://api.test/items/1")
        entry = RequestLogEntry(request=req)
        d = entry.to_dict()
        assert d["response"] is None


class TestLogStore:
    def test_add_and_retrieve(self):
        store = LogStore()
        entry = make_entry()
        store.add(entry)
        assert len(store.all()) == 1
        found = store.get_by_id(entry.request.request_id)
        assert found is entry

    def test_get_by_id_missing(self):
        store = LogStore()
        assert store.get_by_id("nonexistent") is None

    def test_clear(self):
        store = LogStore()
        store.add(make_entry())
        store.clear()
        assert store.all() == []

    def test_save_and_load(self):
        store = LogStore()
        store.add(make_entry(method="POST", status=201))
        store.add(make_entry(method="GET", status=200))

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp_path = f.name

        try:
            store.save_to_file(tmp_path)
            data = json.loads(Path(tmp_path).read_text())
            assert len(data) == 2

            new_store = LogStore()
            new_store.load_from_file(tmp_path)
            entries = new_store.all()
            assert len(entries) == 2
            methods = {e.request.method for e in entries}
            assert methods == {"POST", "GET"}
        finally:
            Path(tmp_path).unlink(missing_ok=True)
