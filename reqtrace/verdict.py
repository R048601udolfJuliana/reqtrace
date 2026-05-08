"""Verdict module: assign pass/fail/skip verdicts to logged request entries."""

from __future__ import annotations

from typing import Optional

VALID_VERDICTS = {"pass", "fail", "skip"}


class VerdictError(Exception):
    """Raised when an invalid verdict is supplied."""


def _validate(verdict: str) -> str:
    v = verdict.strip().lower()
    if v not in VALID_VERDICTS:
        raise VerdictError(
            f"Invalid verdict {verdict!r}. Must be one of: {', '.join(sorted(VALID_VERDICTS))}"
        )
    return v


def set_verdict(entry, verdict: str, reason: Optional[str] = None) -> None:
    """Attach a verdict (pass/fail/skip) to *entry*, optionally with a reason."""
    v = _validate(verdict)
    entry.metadata["verdict"] = v
    if reason is not None:
        entry.metadata["verdict_reason"] = reason.strip()
    elif "verdict_reason" in entry.metadata:
        del entry.metadata["verdict_reason"]


def get_verdict(entry) -> Optional[str]:
    """Return the verdict string for *entry*, or None if unset."""
    return entry.metadata.get("verdict")


def get_verdict_reason(entry) -> Optional[str]:
    """Return the verdict reason for *entry*, or None if unset."""
    return entry.metadata.get("verdict_reason")


def clear_verdict(entry) -> None:
    """Remove verdict (and reason) from *entry*."""
    entry.metadata.pop("verdict", None)
    entry.metadata.pop("verdict_reason", None)


def list_by_verdict(store, verdict: str):
    """Return all entries in *store* whose verdict matches *verdict*."""
    v = _validate(verdict)
    return [e for e in store.all() if e.metadata.get("verdict") == v]


def verdict_summary(store) -> dict:
    """Return a dict with counts for each verdict value across *store*."""
    summary = {v: 0 for v in sorted(VALID_VERDICTS)}
    summary["unset"] = 0
    for entry in store.all():
        v = entry.metadata.get("verdict")
        if v in summary:
            summary[v] += 1
        else:
            summary["unset"] += 1
    return summary
