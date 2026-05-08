"""Tests for reqtrace.rating."""

from __future__ import annotations

import pytest

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.rating import (
    RatingError,
    clear_rating,
    filter_by_min_rating,
    get_comment,
    get_rating,
    list_rated,
    set_rating,
)


def _make_entry(entry_id: str = "abc", method: str = "GET", url: str = "http://example.com/"):
    req = HttpRequest(method=method, url=url, headers={}, body=None)
    return RequestLogEntry(id=entry_id, timestamp="2024-01-01T00:00:00Z", request=req)


def _make_store(*entries):
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


class TestSetRating:
    def test_sets_rating_on_entry(self):
        entry = _make_entry("e1")
        store = _make_store(entry)
        set_rating(store, "e1", 4)
        assert entry.metadata["rating"] == 4

    def test_sets_comment_when_provided(self):
        entry = _make_entry("e2")
        store = _make_store(entry)
        set_rating(store, "e2", 3, comment="Needs work")
        assert entry.metadata["rating_comment"] == "Needs work"

    def test_clears_comment_when_empty(self):
        entry = _make_entry("e3")
        store = _make_store(entry)
        set_rating(store, "e3", 5, comment="Great")
        set_rating(store, "e3", 5, comment="")
        assert "rating_comment" not in entry.metadata

    def test_raises_for_zero_stars(self):
        store = _make_store(_make_entry("e4"))
        with pytest.raises(RatingError):
            set_rating(store, "e4", 0)

    def test_raises_for_six_stars(self):
        store = _make_store(_make_entry("e5"))
        with pytest.raises(RatingError):
            set_rating(store, "e5", 6)

    def test_raises_for_missing_entry(self):
        store = LogStore()
        with pytest.raises(KeyError):
            set_rating(store, "missing", 3)


class TestGetRating:
    def test_returns_none_when_unrated(self):
        entry = _make_entry("u1")
        assert get_rating(entry) is None

    def test_returns_stars_after_set(self):
        entry = _make_entry("u2")
        store = _make_store(entry)
        set_rating(store, "u2", 2)
        assert get_rating(entry) == 2

    def test_get_comment_returns_none_without_comment(self):
        entry = _make_entry("u3")
        store = _make_store(entry)
        set_rating(store, "u3", 1)
        assert get_comment(entry) is None


class TestClearRating:
    def test_removes_rating(self):
        entry = _make_entry("c1")
        store = _make_store(entry)
        set_rating(store, "c1", 5)
        clear_rating(store, "c1")
        assert get_rating(entry) is None

    def test_removes_comment(self):
        entry = _make_entry("c2")
        store = _make_store(entry)
        set_rating(store, "c2", 4, comment="ok")
        clear_rating(store, "c2")
        assert get_comment(entry) is None

    def test_raises_for_missing_entry(self):
        store = LogStore()
        with pytest.raises(KeyError):
            clear_rating(store, "nope")


class TestListAndFilter:
    def test_list_rated_returns_only_rated(self):
        e1 = _make_entry("l1")
        e2 = _make_entry("l2")
        store = _make_store(e1, e2)
        set_rating(store, "l1", 3)
        result = list_rated(store)
        assert len(result) == 1
        assert result[0].id == "l1"

    def test_list_rated_sorted_descending(self):
        e1, e2, e3 = _make_entry("s1"), _make_entry("s2"), _make_entry("s3")
        store = _make_store(e1, e2, e3)
        set_rating(store, "s1", 2)
        set_rating(store, "s2", 5)
        set_rating(store, "s3", 4)
        ids = [e.id for e in list_rated(store)]
        assert ids == ["s2", "s3", "s1"]

    def test_filter_by_min_rating(self):
        e1, e2, e3 = _make_entry("f1"), _make_entry("f2"), _make_entry("f3")
        store = _make_store(e1, e2, e3)
        set_rating(store, "f1", 1)
        set_rating(store, "f2", 3)
        set_rating(store, "f3", 5)
        result = filter_by_min_rating(store, 3)
        ids = {e.id for e in result}
        assert ids == {"f2", "f3"}

    def test_filter_excludes_unrated(self):
        e1 = _make_entry("g1")
        store = _make_store(e1)
        result = filter_by_min_rating(store, 1)
        assert result == []
