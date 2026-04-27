"""Tests for the replay module."""

import unittest
from unittest.mock import MagicMock, patch

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace.replay import replay_request, replay_by_id, ReplayError


def make_entry(method="GET", url="http://example.com/api", body=""):
    req = HttpRequest(
        method=method,
        url=url,
        headers={"Accept": "application/json"},
        body=body,
        host="example.com",
    )
    return RequestLogEntry(request=req)


class TestReplayRequest(unittest.TestCase):

    @patch("reqtrace.replay.http.client.HTTPConnection")
    def test_successful_replay(self, mock_conn_cls):
        mock_conn = MagicMock()
        mock_conn_cls.return_value = mock_conn
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"ok": true}'
        mock_resp.getheaders.return_value = [("Content-Type", "application/json")]
        mock_conn.getresponse.return_value = mock_resp

        entry = make_entry()
        response = replay_request(entry)

        self.assertEqual(response.status_code, 200)
        self.assertIn("ok", response.body)
        mock_conn.request.assert_called_once()

    @patch("reqtrace.replay.http.client.HTTPConnection")
    def test_replay_with_override_host(self, mock_conn_cls):
        mock_conn = MagicMock()
        mock_conn_cls.return_value = mock_conn
        mock_resp = MagicMock()
        mock_resp.status = 404
        mock_resp.read.return_value = b"not found"
        mock_resp.getheaders.return_value = []
        mock_conn.getresponse.return_value = mock_resp

        entry = make_entry()
        replay_request(entry, override_host="localhost:8080")
        mock_conn_cls.assert_called_with("localhost:8080", timeout=10)

    @patch("reqtrace.replay.http.client.HTTPConnection")
    def test_replay_raises_on_connection_error(self, mock_conn_cls):
        mock_conn = MagicMock()
        mock_conn_cls.return_value = mock_conn
        mock_conn.request.side_effect = OSError("connection refused")

        entry = make_entry()
        with self.assertRaises(ReplayError):
            replay_request(entry)


class TestReplayById(unittest.TestCase):

    def test_raises_when_entry_not_found(self):
        store = LogStore()
        with self.assertRaises(ReplayError):
            replay_by_id(store, "nonexistent-id")

    @patch("reqtrace.replay.http.client.HTTPConnection")
    def test_replays_existing_entry(self, mock_conn_cls):
        mock_conn = MagicMock()
        mock_conn_cls.return_value = mock_conn
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b"hello"
        mock_resp.getheaders.return_value = []
        mock_conn.getresponse.return_value = mock_resp

        store = LogStore()
        entry = make_entry()
        store.add(entry)

        response = replay_by_id(store, entry.id)
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
