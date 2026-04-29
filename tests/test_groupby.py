"""Tests for reqtrace.groupby module."""

import pytest
from datetime import datetime

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.groupby import group_entries, group_store, format_groups, GROUP_BY_FIELDS


def _make_entry(
    method="GET",
    url="http://example.com/api/v1",
    status=200,
    include_response=True,
) -> RequestLogEntry:
    req = HttpRequest(method=method, url=url, headers={}, body=None)
    resp = (
        HttpResponse(status_code=status, headers={}, body=None)
        if include_response
        else None
    )
    return RequestLogEntry(
        request=req, response=resp, timestamp=datetime(2024, 1, 1, 12, 0, 0)
    )


class TestGroupEntries:
    def test_group_by_method(self):
        entries = [
            _make_entry(method="GET"),
            _make_entry(method="POST"),
            _make_entry(method="GET"),
        ]
        groups = group_entries(entries, "method")
        assert set(groups.keys()) == {"GET", "POST"}
        assert len(groups["GET"]) == 2
        assert len(groups["POST"]) == 1

    def test_group_by_status(self):
        entries = [
            _make_entry(status=200),
            _make_entry(status=404),
            _make_entry(status=200),
        ]
        groups = group_entries(entries, "status")
        assert set(groups.keys()) == {"200", "404"}
        assert len(groups["200"]) == 2

    def test_group_by_status_no_response(self):
        entries = [_make_entry(include_response=False)]
        groups = group_entries(entries, "status")
        assert "no_response" in groups

    def test_group_by_host(self):
        entries = [
            _make_entry(url="http://alpha.com/x"),
            _make_entry(url="http://beta.com/y"),
            _make_entry(url="http://alpha.com/z"),
        ]
        groups = group_entries(entries, "host")
        assert set(groups.keys()) == {"alpha.com", "beta.com"}
        assert len(groups["alpha.com"]) == 2

    def test_group_by_path(self):
        entries = [
            _make_entry(url="http://example.com/api"),
            _make_entry(url="http://example.com/health"),
            _make_entry(url="http://other.com/api"),
        ]
        groups = group_entries(entries, "path")
        assert "/api" in groups
        assert len(groups["/api"]) == 2

    def test_empty_entries(self):
        groups = group_entries([], "method")
        assert groups == {}

    def test_invalid_field_raises(self):
        with pytest.raises(ValueError, match="Unsupported group-by field"):
            group_entries([_make_entry()], "invalid_field")


class TestGroupStore:
    def test_group_store_delegates(self):
        store = LogStore()
        store.add(_make_entry(method="DELETE"))
        store.add(_make_entry(method="GET"))
        groups = group_store(store, "method")
        assert "DELETE" in groups
        assert "GET" in groups


class TestFormatGroups:
    def test_empty_groups(self):
        assert format_groups({}) == "No entries to group."

    def test_singular_entry_label(self):
        entry = _make_entry()
        result = format_groups({"GET": [entry]})
        assert "1 entry" in result

    def test_plural_entries_label(self):
        entries = [_make_entry(), _make_entry()]
        result = format_groups({"GET": entries})
        assert "2 entries" in result

    def test_sorted_output(self):
        groups = {
            "POST": [_make_entry()],
            "DELETE": [_make_entry()],
            "GET": [_make_entry()],
        }
        lines = format_groups(groups).splitlines()
        keys = [line.split(":")[0] for line in lines]
        assert keys == sorted(keys)
