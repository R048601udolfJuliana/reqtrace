"""Utilities for diffing two HTTP request log entries."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from reqtrace.models import RequestLogEntry


@dataclass
class FieldDiff:
    field: str
    left: Any
    right: Any

    def __str__(self) -> str:
        return f"  {self.field}:\n    - {self.left!r}\n    + {self.right!r}"


@dataclass
class EntryDiff:
    left_id: str
    right_id: str
    diffs: List[FieldDiff]

    @property
    def has_differences(self) -> bool:
        return len(self.diffs) > 0

    def summary(self) -> str:
        if not self.has_differences:
            return f"No differences between {self.left_id} and {self.right_id}."
        lines = [f"Diff {self.left_id} vs {self.right_id}:"]
        for d in self.diffs:
            lines.append(str(d))
        return "\n".join(lines)

    def fields_with_differences(self) -> List[str]:
        """Return a list of field names that have differences."""
        return [d.field for d in self.diffs]


def _compare_requests(left: RequestLogEntry, right: RequestLogEntry) -> List[FieldDiff]:
    diffs: List[FieldDiff] = []

    def check(field: str, a: Any, b: Any) -> None:
        if a != b:
            diffs.append(FieldDiff(field=field, left=a, right=b))

    check("method", left.request.method, right.request.method)
    check("url", left.request.url, right.request.url)
    check("headers", left.request.headers, right.request.headers)
    check("body", left.request.body, right.request.body)
    return diffs


def _compare_responses(
    left: RequestLogEntry, right: RequestLogEntry
) -> List[FieldDiff]:
    diffs: List[FieldDiff] = []
    lr, rr = left.response, right.response

    if lr is None and rr is None:
        return diffs
    if lr is None or rr is None:
        diffs.append(FieldDiff("response", lr, rr))
        return diffs

    def check(field: str, a: Any, b: Any) -> None:
        if a != b:
            diffs.append(FieldDiff(field=field, left=a, right=b))

    check("response.status_code", lr.status_code, rr.status_code)
    check("response.headers", lr.headers, rr.headers)
    check("response.body", lr.body, rr.body)
    return diffs


def diff_entries(left: RequestLogEntry, right: RequestLogEntry) -> EntryDiff:
    """Return an EntryDiff describing differences between two log entries."""
    diffs = _compare_requests(left, right) + _compare_responses(left, right)
    return EntryDiff(left_id=left.id, right_id=right.id, diffs=diffs)


def diff_entries_by_field(
    left: RequestLogEntry, right: RequestLogEntry, fields: List[str]
) -> EntryDiff:
    """Return an EntryDiff restricted to the specified field names.

    Args:
        left: The first log entry to compare.
        right: The second log entry to compare.
        fields: A list of field names to include in the diff (e.g. ``["method",
            "response.status_code"]``). Diffs for fields not in this list are
            excluded from the result.
    """
    full_diff = diff_entries(left, right)
    filtered = [d for d in full_diff.diffs if d.field in fields]
    return EntryDiff(left_id=left.id, right_id=right.id, diffs=filtered)
