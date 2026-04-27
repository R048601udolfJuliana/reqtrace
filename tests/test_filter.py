"""Tests for reqtrace.filter."""
from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from reqtrace.filter import FilterCriteria, apply_filter, build_predicate
from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry


def _make_entry(
    method: str = "GET",
    host: str = "example.com",
    path: str = "/api/v1/items",
    status_code: int | None = 200,
) -> RequestLogEntry:
    req = HttpRequest(
        method=method,
        host=host,
        path=path,
        headers={},
        body=None,
    )
    resp: HttpResponse | None = None
    if status_code is not None:
        resp = HttpResponse(status_code=status_code, headers={}, body=None)
    return RequestLogEntry(
        id=str(uuid.uuid4()),
        timestamp=datetime.utcnow().isoformat(),
        request=req,
        response=resp,
    )


class TestFilterCriteriaMatches:
    def test_no_criteria_matches_all(self):
        entry = _make_entry()
        assert FilterCriteria().matches(entry) is True

    def test_method_match(self):
        entry = _make_entry(method="POST")
        assert FilterCriteria(method="POST").matches(entry) is True

    def test_method_no_match(self):
        entry = _make_entry(method="GET")
        assert FilterCriteria(method="DELETE").matches(entry) is False

    def test_method_case_insensitive(self):
        entry = _make_entry(method="get")
        assert FilterCriteria(method="GET").matches(entry) is True

    def test_host_match(self):
        entry = _make_entry(host="api.local")
        assert FilterCriteria(host="api.local").matches(entry) is True

    def test_host_no_match(self):
        entry = _make_entry(host="other.local")
        assert FilterCriteria(host="api.local").matches(entry) is False

    def test_path_prefix_match(self):
        entry = _make_entry(path="/api/v1/users")
        assert FilterCriteria(path_prefix="/api/v1").matches(entry) is True

    def test_path_prefix_no_match(self):
        entry = _make_entry(path="/health")
        assert FilterCriteria(path_prefix="/api").matches(entry) is False

    def test_status_code_match(self):
        entry = _make_entry(status_code=404)
        assert FilterCriteria(status_code=404).matches(entry) is True

    def test_status_code_no_match(self):
        entry = _make_entry(status_code=200)
        assert FilterCriteria(status_code=500).matches(entry) is False

    def test_status_code_no_response(self):
        entry = _make_entry(status_code=None)
        assert FilterCriteria(status_code=200).matches(entry) is False

    def test_has_response_true(self):
        assert FilterCriteria(has_response=True).matches(_make_entry(status_code=200)) is True
        assert FilterCriteria(has_response=True).matches(_make_entry(status_code=None)) is False

    def test_has_response_false(self):
        assert FilterCriteria(has_response=False).matches(_make_entry(status_code=None)) is True
        assert FilterCriteria(has_response=False).matches(_make_entry(status_code=200)) is False


class TestApplyFilter:
    def test_returns_matching_entries(self):
        entries = [
            _make_entry(method="GET"),
            _make_entry(method="POST"),
            _make_entry(method="GET"),
        ]
        result = apply_filter(entries, FilterCriteria(method="GET"))
        assert len(result) == 2

    def test_empty_input(self):
        assert apply_filter([], FilterCriteria(method="GET")) == []

    def test_combined_criteria(self):
        entries = [
            _make_entry(method="GET", status_code=200),
            _make_entry(method="GET", status_code=404),
            _make_entry(method="POST", status_code=200),
        ]
        result = apply_filter(entries, FilterCriteria(method="GET", status_code=200))
        assert len(result) == 1


class TestBuildPredicate:
    def test_predicate_is_callable(self):
        pred = build_predicate(method="GET")
        assert callable(pred)

    def test_predicate_filters_correctly(self):
        pred = build_predicate(path_prefix="/admin")
        assert pred(_make_entry(path="/admin/users")) is True
        assert pred(_make_entry(path="/api/users")) is False
