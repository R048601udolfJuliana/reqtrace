"""Assertion helpers for validating logged HTTP responses against expectations."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from reqtrace.models import RequestLogEntry


@dataclass
class AssertionFailure:
    field: str
    expected: Any
    actual: Any

    def __str__(self) -> str:
        return f"{self.field}: expected {self.expected!r}, got {self.actual!r}"


@dataclass
class AssertionResult:
    entry_id: str
    failures: List[AssertionFailure] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.failures) == 0

    def summary(self) -> str:
        if self.passed:
            return f"[PASS] {self.entry_id}: all assertions passed"
        lines = [f"[FAIL] {self.entry_id}: {len(self.failures)} failure(s)"]
        for f in self.failures:
            lines.append(f"  - {f}")
        return "\n".join(lines)


def assert_entry(
    entry: RequestLogEntry,
    *,
    status: Optional[int] = None,
    body_contains: Optional[str] = None,
    headers_contain: Optional[Dict[str, str]] = None,
    max_latency_ms: Optional[float] = None,
) -> AssertionResult:
    """Assert properties of the response attached to *entry*."""
    result = AssertionResult(entry_id=entry.id)
    resp = entry.response

    if status is not None:
        actual_status = resp.status_code if resp else None
        if actual_status != status:
            result.failures.append(
                AssertionFailure("status_code", status, actual_status)
            )

    if body_contains is not None:
        actual_body = (resp.body or "") if resp else ""
        if body_contains not in actual_body:
            snippet = actual_body[:80] if actual_body else ""
            result.failures.append(
                AssertionFailure("body_contains", body_contains, snippet)
            )

    if headers_contain:
        actual_headers = (resp.headers or {}) if resp else {}
        for key, value in headers_contain.items():
            actual_val = actual_headers.get(key)
            if actual_val != value:
                result.failures.append(
                    AssertionFailure(f"header[{key}]", value, actual_val)
                )

    if max_latency_ms is not None:
        latency = entry.metadata.get("latency_ms") if entry.metadata else None
        if latency is None or float(latency) > max_latency_ms:
            result.failures.append(
                AssertionFailure("latency_ms", f"<= {max_latency_ms}", latency)
            )

    return result
