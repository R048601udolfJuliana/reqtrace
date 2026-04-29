"""Tests for reqtrace.cmd_anonymize module."""

import pytest
from unittest.mock import MagicMock, patch
from argparse import Namespace

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.cmd_anonymize import cmd_anonymize
from reqtrace.anonymize import REDACTED


def _make_entry(auth="Bearer token"):
    req = HttpRequest(
        method="GET",
        url="http://api.example.com/v1/data",
        headers={"Authorization": auth, "Accept": "application/json"},
        body=None,
    )
    resp = HttpResponse(status_code=200, headers={"Content-Type": "application/json"}, body="{}", elapsed_ms=10)
    return RequestLogEntry(request=req, response=resp)


def _make_store(*entries):
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


class TestCmdAnonymize:
    def test_anonymizes_all_entries(self, capsys):
        e1 = _make_entry()
        e2 = _make_entry(auth="Bearer other")
        store = _make_store(e1, e2)
        args = Namespace(id=None, header=None, body_pattern=None)
        cmd_anonymize(args, store)
        captured = capsys.readouterr()
        assert "2" in captured.out
        for entry in store.all():
            assert entry.request.headers["Authorization"] == REDACTED

    def test_anonymizes_single_entry_by_id(self, capsys):
        e1 = _make_entry()
        e2 = _make_entry(auth="Bearer other")
        store = _make_store(e1, e2)
        args = Namespace(id=e1.id, header=None, body_pattern=None)
        cmd_anonymize(args, store)
        assert store.get_by_id(e1.id).request.headers["Authorization"] == REDACTED
        assert store.get_by_id(e2.id).request.headers["Authorization"] == "Bearer other"

    def test_missing_id_prints_message(self, capsys):
        store = _make_store()
        args = Namespace(id="nonexistent-id", header=None, body_pattern=None)
        cmd_anonymize(args, store)
        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_extra_header_flag_redacted(self, capsys):
        req = HttpRequest(
            method="GET",
            url="http://example.com",
            headers={"X-Api-Key": "mykey", "Accept": "*/*"},
            body=None,
        )
        entry = RequestLogEntry(request=req, response=None)
        store = _make_store(entry)
        args = Namespace(id=None, header=["X-Api-Key"], body_pattern=None)
        cmd_anonymize(args, store)
        updated = store.get_by_id(entry.id)
        assert updated.request.headers["X-Api-Key"] == REDACTED
        assert updated.request.headers["Accept"] == "*/*"
