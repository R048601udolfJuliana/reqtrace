"""Tests for reqtrace.expire."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta

import pytest

from reqtrace.models import HttpRequest, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.expire import (
    set_expiry,
    get_expiry,
    is_expired,
    clear_expiry,
    list_expired,
    purge_expired,
)


def _make_entry(url: str = "http://example.com/api") -> RequestLogEntry:
    req = HttpRequest(method="GET", url=url, headers={}, body=None)
    return RequestLogEntry(
        id=str(uuid.uuid4()),
        timestamp="2024-01-01T00:00:00Z",
        request=req,
        response=None,
        metadata={},
    )


def _make_store(*entries: RequestLogEntry) -> LogStore:
    store = LogStore()
    for e in entries:
        store.add(e)
    return store


class TestSetExpiry:
    def test_sets_expire_at_in_metadata(self):
        entry = _make_entry()
        set_expiry(entry, ttl_seconds=60)
        assert "expire_at" in entry.metadata

    def test_expire_at_is_in_the_future(self):
        entry = _make_entry()
        before = datetime.now(timezone.utc)
        set_expiry(entry, ttl_seconds=300)
        expiry = get_expiry(entry)
        assert expiry > before

    def test_raises_for_zero_ttl(self):
        entry = _make_entry()
        with pytest.raises(ValueError):
            set_expiry(entry, ttl_seconds=0)

    def test_raises_for_negative_ttl(self):
        entry = _make_entry()
        with pytest.raises(ValueError):
            set_expiry(entry, ttl_seconds=-10)

    def test_returns_entry(self):
        entry = _make_entry()
        result = set_expiry(entry, ttl_seconds=1)
        assert result is entry


class TestGetExpiry:
    def test_returns_none_when_not_set(self):
        entry = _make_entry()
        assert get_expiry(entry) is None

    def test_returns_datetime_when_set(self):
        entry = _make_entry()
        set_expiry(entry, ttl_seconds=120)
        result = get_expiry(entry)
        assert isinstance(result, datetime)


class TestIsExpired:
    def test_not_expired_when_no_expiry(self):
        entry = _make_entry()
        assert is_expired(entry) is False

    def test_not_expired_before_expiry(self):
        entry = _make_entry()
        set_expiry(entry, ttl_seconds=3600)
        assert is_expired(entry) is False

    def test_expired_when_now_is_past_expiry(self):
        entry = _make_entry()
        set_expiry(entry, ttl_seconds=60)
        future_now = datetime.now(timezone.utc) + timedelta(seconds=120)
        assert is_expired(entry, now=future_now) is True

    def test_expired_exactly_at_expiry_time(self):
        entry = _make_entry()
        set_expiry(entry, ttl_seconds=60)
        exact_now = get_expiry(entry)
        assert is_expired(entry, now=exact_now) is True


class TestClearExpiry:
    def test_removes_expire_at_key(self):
        entry = _make_entry()
        set_expiry(entry, ttl_seconds=60)
        clear_expiry(entry)
        assert "expire_at" not in entry.metadata

    def test_no_error_when_not_set(self):
        entry = _make_entry()
        clear_expiry(entry)  # should not raise

    def test_returns_entry(self):
        entry = _make_entry()
        result = clear_expiry(entry)
        assert result is entry


class TestListAndPurgeExpired:
    _PAST = datetime.now(timezone.utc) - timedelta(seconds=1)
    _FUTURE = datetime.now(timezone.utc) + timedelta(seconds=3600)

    def test_list_expired_empty_store(self):
        store = _make_store()
        assert list_expired(store) == []

    def test_list_expired_finds_expired_entries(self):
        e1 = _make_entry("http://a.com")
        e2 = _make_entry("http://b.com")
        set_expiry(e1, ttl_seconds=60)
        store = _make_store(e1, e2)
        result = list_expired(store, now=self._FUTURE)
        assert e1 in result
        assert e2 not in result

    def test_purge_expired_removes_entries(self):
        e1 = _make_entry("http://a.com")
        e2 = _make_entry("http://b.com")
        set_expiry(e1, ttl_seconds=60)
        store = _make_store(e1, e2)
        count = purge_expired(store, now=self._FUTURE)
        assert count == 1
        assert store.get_by_id(e1.id) is None
        assert store.get_by_id(e2.id) is not None

    def test_purge_returns_zero_when_nothing_expired(self):
        e1 = _make_entry()
        store = _make_store(e1)
        assert purge_expired(store) == 0
