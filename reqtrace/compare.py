"""Side-by-side comparison of two log entries with similarity scoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from reqtrace.models import RequestLogEntry


@dataclass
class CompareResult:
    entry_a: RequestLogEntry
    entry_b: RequestLogEntry
    score: float  # 0.0 (completely different) – 1.0 (identical)
    field_scores: dict[str, float] = field(default_factory=dict)

    @property
    def summary(self) -> str:
        pct = int(self.score * 100)
        return f"Similarity: {pct}%  (" + ", ".join(
            f"{k}={int(v*100)}%" for k, v in self.field_scores.items()
        ) + ")"


def _str_similarity(a: str, b: str) -> float:
    """Simple character-level Jaccard similarity."""
    if a == b:
        return 1.0
    if not a and not b:
        return 1.0
    set_a = set(a)
    set_b = set(b)
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union) if union else 0.0


def _header_similarity(ha: dict, hb: dict) -> float:
    keys_a = set(k.lower() for k in ha)
    keys_b = set(k.lower() for k in hb)
    all_keys = keys_a | keys_b
    if not all_keys:
        return 1.0
    matches = sum(
        1 for k in all_keys
        if ha.get(k, ha.get(k.upper(), "")) == hb.get(k, hb.get(k.upper(), ""))
    )
    return matches / len(all_keys)


def compare_entries(
    entry_a: RequestLogEntry,
    entry_b: RequestLogEntry,
    weights: Optional[dict[str, float]] = None,
) -> CompareResult:
    """Compare two entries and return a CompareResult with a similarity score."""
    if weights is None:
        weights = {"method": 0.2, "url": 0.4, "headers": 0.2, "body": 0.2}

    ra, rb = entry_a.request, entry_b.request

    method_score = 1.0 if ra.method.upper() == rb.method.upper() else 0.0
    url_score = _str_similarity(ra.url, rb.url)
    header_score = _header_similarity(ra.headers or {}, rb.headers or {})
    body_score = _str_similarity(ra.body or "", rb.body or "")

    field_scores = {
        "method": method_score,
        "url": url_score,
        "headers": header_score,
        "body": body_score,
    }

    total_weight = sum(weights.values())
    score = sum(field_scores[k] * weights.get(k, 0.0) for k in field_scores) / total_weight

    return CompareResult(
        entry_a=entry_a,
        entry_b=entry_b,
        score=round(score, 4),
        field_scores={k: round(v, 4) for k, v in field_scores.items()},
    )
