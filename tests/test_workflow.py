"""Tests for reqtrace.workflow and reqtrace.cmd_workflow."""

from __future__ import annotations

import types
import unittest
from unittest.mock import MagicMock

from reqtrace.workflow import (
    WorkflowError,
    clear_workflow,
    filter_by_stage,
    filter_by_workflow,
    get_workflow,
    set_workflow,
    update_stage,
)
from reqtrace.cmd_workflow import cmd_workflow


def _make_entry(entry_id: str = "abc123"):
    entry = MagicMock()
    entry.id = entry_id
    entry.metadata = {}
    return entry


def _make_store(*entries):
    store = MagicMock()
    store.all.return_value = list(entries)
    store.get_by_id.side_effect = lambda eid: next(
        (e for e in entries if e.id == eid), None
    )
    return store


class TestSetWorkflow(unittest.TestCase):
    def test_sets_name_and_stage(self):
        e = _make_entry()
        set_workflow(e, "release-1", "in_progress")
        self.assertEqual(e.metadata["workflow"], "release-1")
        self.assertEqual(e.metadata["workflow_stage"], "in_progress")

    def test_default_stage_is_pending(self):
        e = _make_entry()
        set_workflow(e, "hotfix")
        self.assertEqual(e.metadata["workflow_stage"], "pending")

    def test_invalid_stage_raises(self):
        e = _make_entry()
        with self.assertRaises(WorkflowError):
            set_workflow(e, "wf", "unknown_stage")

    def test_normalises_stage_to_lowercase(self):
        e = _make_entry()
        set_workflow(e, "wf", "DONE")
        self.assertEqual(e.metadata["workflow_stage"], "done")


class TestGetWorkflow(unittest.TestCase):
    def test_returns_none_when_not_set(self):
        e = _make_entry()
        self.assertIsNone(get_workflow(e))

    def test_returns_dict_when_set(self):
        e = _make_entry()
        set_workflow(e, "sprint", "review")
        wf = get_workflow(e)
        self.assertEqual(wf, {"name": "sprint", "stage": "review"})


class TestUpdateStage(unittest.TestCase):
    def test_updates_stage(self):
        e = _make_entry()
        set_workflow(e, "wf", "pending")
        update_stage(e, "done")
        self.assertEqual(e.metadata["workflow_stage"], "done")

    def test_raises_if_no_workflow(self):
        e = _make_entry()
        with self.assertRaises(WorkflowError):
            update_stage(e, "done")

    def test_raises_on_invalid_stage(self):
        e = _make_entry()
        set_workflow(e, "wf")
        with self.assertRaises(WorkflowError):
            update_stage(e, "nope")


class TestClearWorkflow(unittest.TestCase):
    def test_removes_metadata(self):
        e = _make_entry()
        set_workflow(e, "wf", "done")
        clear_workflow(e)
        self.assertIsNone(get_workflow(e))

    def test_clear_on_clean_entry_is_safe(self):
        e = _make_entry()
        clear_workflow(e)  # should not raise


class TestFilterHelpers(unittest.TestCase):
    def setUp(self):
        self.e1 = _make_entry("1")
        self.e2 = _make_entry("2")
        self.e3 = _make_entry("3")
        set_workflow(self.e1, "alpha", "pending")
        set_workflow(self.e2, "alpha", "done")
        set_workflow(self.e3, "beta", "done")

    def test_filter_by_workflow_name(self):
        result = filter_by_workflow([self.e1, self.e2, self.e3], "alpha")
        self.assertEqual([e.id for e in result], ["1", "2"])

    def test_filter_by_stage(self):
        result = filter_by_stage([self.e1, self.e2, self.e3], "done")
        self.assertEqual([e.id for e in result], ["2", "3"])

    def test_filter_by_workflow_case_insensitive(self):
        result = filter_by_workflow([self.e1, self.e2], "ALPHA")
        self.assertEqual(len(result), 2)


class TestCmdWorkflow(unittest.TestCase):
    def _args(self, **kwargs):
        base = types.SimpleNamespace(
            workflow_action="set", id="abc", name="wf", stage="pending"
        )
        for k, v in kwargs.items():
            setattr(base, k, v)
        return base

    def test_set_prints_confirmation(self):
        e = _make_entry("abc")
        store = _make_store(e)
        args = self._args(workflow_action="set", id="abc", name="sprint", stage="pending")
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cmd_workflow(args, store)
        self.assertIn("sprint", buf.getvalue())

    def test_set_missing_entry(self):
        store = _make_store()
        args = self._args(workflow_action="set", id="missing", name="wf", stage="pending")
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cmd_workflow(args, store)
        self.assertIn("not found", buf.getvalue())

    def test_show_no_workflow(self):
        e = _make_entry("x")
        store = _make_store(e)
        args = self._args(workflow_action="show", id="x")
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cmd_workflow(args, store)
        self.assertIn("No workflow", buf.getvalue())
