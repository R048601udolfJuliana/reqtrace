"""Retry logic for replaying failed requests with configurable back-off."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from reqtrace.models import RequestLogEntry
from reqtrace.replay import ReplayError, replay_request


@dataclass
class RetryPolicy:
    """Configuration for retry behaviour."""

    max_attempts: int = 3
    backoff_base: float = 1.0   # seconds between attempts (multiplied by attempt index)
    retry_on_status: List[int] = field(default_factory=lambda: [500, 502, 503, 504])
    override_host: Optional[str] = None


@dataclass
class RetryResult:
    """Outcome of a retry run."""

    attempts: int
    final_status: Optional[int]
    success: bool
    error: Optional[str] = None


def _should_retry(status: Optional[int], policy: RetryPolicy) -> bool:
    if status is None:
        return True
    return status in policy.retry_on_status


def retry_entry(
    entry: RequestLogEntry,
    policy: RetryPolicy,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> RetryResult:
    """Replay *entry* up to policy.max_attempts times.

    Returns a :class:`RetryResult` describing what happened.
    """
    last_status: Optional[int] = None
    last_error: Optional[str] = None

    for attempt in range(1, policy.max_attempts + 1):
        try:
            response = replay_request(entry, override_host=policy.override_host)
            last_status = response.status_code
            if not _should_retry(last_status, policy):
                return RetryResult(
                    attempts=attempt,
                    final_status=last_status,
                    success=True,
                )
        except ReplayError as exc:
            last_error = str(exc)
            last_status = None

        if attempt < policy.max_attempts:
            sleep_fn(policy.backoff_base * attempt)

    return RetryResult(
        attempts=policy.max_attempts,
        final_status=last_status,
        success=False,
        error=last_error,
    )
