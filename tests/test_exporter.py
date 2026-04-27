"""Tests for reqtrace.exporter module."""

import json
import datetime
import pytest

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.exporter import entry_to_curl, entry_to_dict, export_json, export_curl


FIXED_TS = datetime.datetime(2024, 1, 15, 10, 30, 0)


def make_entry(with_response: bool = True) -> RequestLogEntry:
    req = HttpRequest(
        method="POST",
        url="http://api.example.com/items",
        headers={"Content-Type": "application/json", "X-Token": "abc123"},
        body='{"name": "widget"}',
    )
    resp = None
    if with_response:
        resp = HttpResponse(
            status_code=201,
            headers={"Content-Type": "application/json"},
            body='{"id": 42}',
        )
    entry = RequestLogEntry(request=req, response=resp)
    entry.timestamp = FIXED_TS
    return entry


class TestEntryToDict:
    def test_contains_id_and_timestamp(self):
        entry = make_entry()
        d = entry_to_dict(entry)
        assert d["id"] == entry.id
        assert d["timestamp"] == FIXED_TS.isoformat()

    def test_contains_request(self):
        entry = make_entry()
        d = entry_to_dict(entry)
        assert d["request"]["method"] == "POST"
        assert d["request"]["url"] == "http://api.example.com/items"

    def test_contains_response_when_present(self):
        entry = make_entry(with_response=True)
        d = entry_to_dict(entry)
        assert "response" in d
        assert d["response"]["status_code"] == 201

    def test_no_response_key_when_absent(self):
        entry = make_entry(with_response=False)
        d = entry_to_dict(entry)
        assert "response" not in d


class TestExportJson:
    def test_returns_valid_json(self):
        entries = [make_entry(), make_entry(with_response=False)]
        result = export_json(entries)
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 2

    def test_empty_list(self):
        assert export_json([]) == "[]"


class TestEntryToCurl:
    def test_includes_method_and_url(self):
        entry = make_entry()
        cmd = entry_to_curl(entry)
        assert "-X POST" in cmd
        assert "http://api.example.com/items" in cmd

    def test_includes_custom_headers(self):
        entry = make_entry()
        cmd = entry_to_curl(entry)
        assert "-H" in cmd
        assert "X-Token: abc123" in cmd

    def test_skips_host_header(self):
        req = HttpRequest(
            method="GET",
            url="http://example.com/",
            headers={"Host": "example.com"},
            body=None,
        )
        entry = RequestLogEntry(request=req)
        cmd = entry_to_curl(entry)
        assert "Host" not in cmd

    def test_includes_body(self):
        entry = make_entry()
        cmd = entry_to_curl(entry)
        assert "--data" in cmd
        assert 'widget' in cmd


class TestExportCurl:
    def test_multiple_entries_separated_by_newline(self):
        entries = [make_entry(), make_entry()]
        result = export_curl(entries)
        lines = result.split("\n")
        assert len(lines) == 2
        for line in lines:
            assert line.startswith("curl")
