"""Workflow: attach a named workflow/stage label to log entries for pipeline tracking."""

from __future__ import annotations

from typing import List, Optional

WORKFLOW_KEY = "workflow"
STAGE_KEY = "workflow_stage"

_VALID_STAGES = {"pending", "in_progress", "review", "done", "blocked"}


class WorkflowError(ValueError):
    """Raised when an invalid workflow stage is supplied."""


def set_workflow(entry, name: str, stage: str = "pending") -> None:
    """Attach a workflow *name* and *stage* to *entry*.

    Raises WorkflowError if *stage* is not one of the recognised values.
    """
    stage = stage.lower().strip()
    if stage not in _VALID_STAGES:
        raise WorkflowError(
            f"Unknown stage {stage!r}. Valid stages: {sorted(_VALID_STAGES)}"
        )
    entry.metadata[WORKFLOW_KEY] = name.strip()
    entry.metadata[STAGE_KEY] = stage


def get_workflow(entry) -> Optional[dict]:
    """Return the workflow dict for *entry*, or None if not set."""
    name = entry.metadata.get(WORKFLOW_KEY)
    if name is None:
        return None
    return {
        "name": name,
        "stage": entry.metadata.get(STAGE_KEY, "pending"),
    }


def update_stage(entry, stage: str) -> None:
    """Update only the stage of an already-attached workflow.

    Raises WorkflowError if no workflow is attached or if *stage* is invalid.
    """
    if WORKFLOW_KEY not in entry.metadata:
        raise WorkflowError("No workflow attached to this entry.")
    stage = stage.lower().strip()
    if stage not in _VALID_STAGES:
        raise WorkflowError(
            f"Unknown stage {stage!r}. Valid stages: {sorted(_VALID_STAGES)}"
        )
    entry.metadata[STAGE_KEY] = stage


def clear_workflow(entry) -> None:
    """Remove workflow metadata from *entry*."""
    entry.metadata.pop(WORKFLOW_KEY, None)
    entry.metadata.pop(STAGE_KEY, None)


def filter_by_workflow(entries: List, name: str) -> List:
    """Return entries that belong to workflow *name* (case-insensitive)."""
    name_lower = name.lower().strip()
    return [
        e for e in entries
        if e.metadata.get(WORKFLOW_KEY, "").lower() == name_lower
    ]


def filter_by_stage(entries: List, stage: str) -> List:
    """Return entries whose workflow stage matches *stage* (case-insensitive)."""
    stage_lower = stage.lower().strip()
    return [
        e for e in entries
        if e.metadata.get(STAGE_KEY, "").lower() == stage_lower
    ]
