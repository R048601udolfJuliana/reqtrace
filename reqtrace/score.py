"""Score entries based on heuristics for debugging interest."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from reqtrace.models import RequestLogEntry

# Weights for each signal
_W_ERROR_STATUS = 40
_W_SLOW_RESPONSE = 20
_W_LARGE_BODY = 10
_W_HAS_NOTE = 15
_W_IS_PINNED = 25
_W_IS_BOOKMARKED = 10
_W_RETRY_METHOD = 5  # PUT/DELETE/PATCH are more interesting than GET

_SLOW_THRESHOLD_MS = 1000
_LARGE_BODY_BYTES = 10_000


@dataclass
class ScoredEntry:
    entry: RequestLogEntry
    score: int
    reasons: List[str]

    def summary(self) -> str:
        tag = ", ".join(self.reasons) if self.reasons else "no signals"
        return f"[score={self.score}] {self.entry.request.method} {self.entry.request.url} ({tag})"


def score_entry(entry: RequestLogEntry) -> ScoredEntry:
    """Compute a debug-interest score for a single log entry."""
    score = 0
    reasons: List[str] = []

    resp = entry.response
    if resp is not None:
        if resp.status_code >= 400:
            score += _W_ERROR_STATUS
            reasons.append(f"status={resp.status_code}")

        elapsed = entry.metadata.get("elapsed_ms")
        if elapsed is not None and elapsed >= _SLOW_THRESHOLD_MS:
            score += _W_SLOW_RESPONSE
            reasons.append(f"slow={elapsed}ms")

        body_len = len(resp.body.encode() if isinstance(resp.body, str) else (resp.body or b""))
        if body_len >= _LARGE_BODY_BYTES:
            score += _W_LARGE_BODY
            reasons.append("large-response-body")

    method = entry.request.method.upper()
    if method in {"PUT", "DELETE", "PATCH"}:
        score += _W_RETRY_METHOD
        reasons.append(f"method={method}")

    tags = set(entry.metadata.get("tags", []))
    if "pinned" in tags:
        score += _W_IS_PINNED
        reasons.append("pinned")
    if "bookmark" in tags:
        score += _W_IS_BOOKMARKED
        reasons.append("bookmarked")

    notes = entry.metadata.get("notes", [])
    if notes:
        score += _W_HAS_NOTE
        reasons.append("has-notes")

    return ScoredEntry(entry=entry, score=score, reasons=reasons)


def rank_entries(entries: List[RequestLogEntry], top: int = 0) -> List[ScoredEntry]:
    """Return entries sorted by descending score.

    Args:
        entries: list of log entries to rank.
        top: if > 0, return only the top-N results.
    """
    scored = [score_entry(e) for e in entries]
    scored.sort(key=lambda s: s.score, reverse=True)
    if top > 0:
        scored = scored[:top]
    return scored
