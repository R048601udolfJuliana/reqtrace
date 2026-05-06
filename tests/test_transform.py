"""Tests for reqtrace.transform and reqtrace.cmd_transform."""

from __future__ import annotations

import argparse
import copy
from unittest.mock import MagicMock

import pytest

from reqtrace.models import HttpRequest, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.transform import (
    apply_transforms,
    build_transform_pipeline,
    remove_header,
    replace_body,
    rewrite_url,
    set_header,
)
from reqtrace.cmd_transform import cmd_transform


def _make_entry(entry_id: str = "abc", url: str = "http://example.com/api") -> RequestLogEntry:
    req = HttpRequest(
        method="GET",
        url=url,
        headers={"Authorization": "Bearer token", "Accept": "application/json"},
        body=None,
    )
    return RequestLogEntry(id=entry_id, timestamp="2024-01-01T00:00:00", request=req)


def _make_store(*entries) -> LogStore:
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


# ---------------------------------------------------------------------------
# Unit tests for transform primitives
# ---------------------------------------------------------------------------

class TestSetHeader:
    def test_adds_new_header(self):
        entry = _make_entry()
        result = set_header(entry, "X-Custom", "hello")
        assert result.request.headers["X-Custom"] == "hello"

    def test_overwrites_existing_header(self):
        entry = _make_entry()
        result = set_header(entry, "Accept", "text/plain")
        assert result.request.headers["Accept"] == "text/plain"


class TestRemoveHeader:
    def test_removes_existing_header(self):
        entry = _make_entry()
        result = remove_header(entry, "Authorization")
        assert "Authorization" not in result.request.headers

    def test_case_insensitive_removal(self):
        entry = _make_entry()
        result = remove_header(entry, "authorization")
        assert "Authorization" not in result.request.headers

    def test_missing_header_is_noop(self):
        entry = _make_entry()
        before = dict(entry.request.headers)
        result = remove_header(entry, "X-Does-Not-Exist")
        assert result.request.headers == before


class TestReplaceBody:
    def test_sets_body(self):
        entry = _make_entry()
        result = replace_body(entry, '{"key": "value"}')
        assert result.request.body == '{"key": "value"}'

    def test_clears_body_with_none(self):
        entry = _make_entry()
        entry.request.body = "old body"
        result = replace_body(entry, None)
        assert result.request.body is None


class TestRewriteUrl:
    def test_replaces_host(self):
        entry = _make_entry(url="http://old.host/path")
        result = rewrite_url(entry, "old.host", "new.host")
        assert result.request.url == "http://new.host/path"

    def test_only_first_occurrence_replaced(self):
        entry = _make_entry(url="http://a.com/a/path")
        result = rewrite_url(entry, "/a", "/b")
        assert result.request.url == "http://a.com/b/path"


class TestBuildPipelineAndApply:
    def test_empty_pipeline_is_identity(self):
        entry = _make_entry()
        original_url = entry.request.url
        pipeline = build_transform_pipeline()
        result = apply_transforms(entry, pipeline)
        assert result.request.url == original_url

    def test_combined_pipeline(self):
        entry = _make_entry(url="http://staging.example.com/api")
        pipeline = build_transform_pipeline(
            set_headers={"X-Env": "prod"},
            remove_headers=["Authorization"],
            body="{}",
            url_rewrite=("staging", "prod"),
        )
        result = apply_transforms(entry, pipeline)
        assert result.request.headers.get("X-Env") == "prod"
        assert "Authorization" not in result.request.headers
        assert result.request.body == "{}"
        assert "prod.example.com" in result.request.url


# ---------------------------------------------------------------------------
# cmd_transform integration
# ---------------------------------------------------------------------------

def _args(**kwargs) -> argparse.Namespace:
    defaults = dict(id=None, set_header=None, remove_header=None, body=None, url_rewrite=None)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdTransform:
    def test_no_transforms_prints_nothing_to_do(self, capsys):
        store = _make_store(_make_entry())
        cmd_transform(_args(), store)
        assert "nothing to do" in capsys.readouterr().out

    def test_set_header_applied_to_all(self, capsys):
        e1 = _make_entry("id1")
        e2 = _make_entry("id2")
        store = _make_store(e1, e2)
        cmd_transform(_args(set_header=["X-Foo=bar"]), store)
        out = capsys.readouterr().out
        assert "2 entry" in out

    def test_targets_single_entry_by_id(self, capsys):
        e1 = _make_entry("id1")
        e2 = _make_entry("id2")
        store = _make_store(e1, e2)
        cmd_transform(_args(id="id1", set_header=["X-Single=yes"]), store)
        out = capsys.readouterr().out
        assert "1 entry" in out

    def test_missing_id_prints_not_found(self, capsys):
        store = _make_store()
        cmd_transform(_args(id="missing", set_header=["X-A=B"]), store)
        assert "not found" in capsys.readouterr().out

    def test_invalid_set_header_format(self, capsys):
        store = _make_store(_make_entry())
        cmd_transform(_args(set_header=["badvalue"]), store)
        assert "invalid" in capsys.readouterr().out

    def test_invalid_url_rewrite_format(self, capsys):
        store = _make_store(_make_entry())
        cmd_transform(_args(url_rewrite="nocolon", set_header=["X=Y"]), store)
        assert "--url-rewrite" in capsys.readouterr().out
