"""Tests for the CLI module."""

import unittest
from io import StringIO
from unittest.mock import patch, MagicMock

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.storage import LogStore
from reqtrace import cli


def make_store_with_entry():
    req = HttpRequest(
        method="POST",
        url="http://api.local/items",
        headers={},
        body='{"name": "test"}',
        host="api.local",
    )
    resp = HttpResponse(status_code=201, headers={}, body='{"id": 1}')
    entry = RequestLogEntry(request=req, response=resp)
    store = LogStore()
    store.add(entry)
    return store, entry


class TestCmdList(unittest.TestCase):

    def test_list_empty(self):
        store = LogStore()
        args = MagicMock()
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            cli.cmd_list(store, args)
            self.assertIn("No recorded", mock_out.getvalue())

    def test_list_with_entries(self):
        store, entry = make_store_with_entry()
        args = MagicMock()
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            cli.cmd_list(store, args)
            output = mock_out.getvalue()
        self.assertIn(entry.id, output)
        self.assertIn("POST", output)
        self.assertIn("201", output)


class TestCmdShow(unittest.TestCase):

    def test_show_existing(self):
        store, entry = make_store_with_entry()
        args = MagicMock(id=entry.id)
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            cli.cmd_show(store, args)
            self.assertIn(entry.id, mock_out.getvalue())

    def test_show_missing_exits(self):
        store = LogStore()
        args = MagicMock(id="bad-id")
        with self.assertRaises(SystemExit):
            cli.cmd_show(store, args)


class TestCmdReplay(unittest.TestCase):

    @patch("reqtrace.cli.replay_by_id")
    def test_replay_prints_status(self, mock_replay):
        mock_replay.return_value = HttpResponse(status_code=200, headers={}, body="OK")
        store, entry = make_store_with_entry()
        args = MagicMock(id=entry.id, host=None, verbose=False)
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            cli.cmd_replay(store, args)
            self.assertIn("200", mock_out.getvalue())

    @patch("reqtrace.cli.replay_by_id")
    def test_replay_error_exits(self, mock_replay):
        from reqtrace.replay import ReplayError
        mock_replay.side_effect = ReplayError("timeout")
        store, entry = make_store_with_entry()
        args = MagicMock(id=entry.id, host=None, verbose=False)
        with self.assertRaises(SystemExit):
            cli.cmd_replay(store, args)


if __name__ == "__main__":
    unittest.main()
