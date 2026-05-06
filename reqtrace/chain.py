"""Chain multiple stored requests into a sequential replay session."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from reqtrace.replay import replay_request, ReplayError
from reqtrace.storage import LogStore


@dataclass
class ChainStep:
    entry_id: str
    override_host: Optional[str] = None
    stop_on_error: bool = True


@dataclass
class ChainStepResult:
    entry_id: str
    success: bool
    status_code: Optional[int] = None
    error: Optional[str] = None

    def __str__(self) -> str:
        if self.success:
            return f"[OK]   {self.entry_id} -> HTTP {self.status_code}"
        return f"[FAIL] {self.entry_id} -> {self.error}"


@dataclass
class ChainResult:
    steps: List[ChainStepResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(s.success for s in self.steps)

    @property
    def failed_count(self) -> int:
        return sum(1 for s in self.steps if not s.success)

    def summary(self) -> str:
        total = len(self.steps)
        passed = total - self.failed_count
        lines = [f"Chain: {passed}/{total} steps passed"]
        for step in self.steps:
            lines.append(f"  {step}")
        return "\n".join(lines)


def run_chain(store: LogStore, steps: List[ChainStep]) -> ChainResult:
    """Replay a sequence of stored requests in order.

    Args:
        store: The log store containing the entries to replay.
        steps: Ordered list of ChainStep descriptors.

    Returns:
        A ChainResult summarising each step outcome.
    """
    result = ChainResult()

    for step in steps:
        entry = store.get_by_id(step.entry_id)
        if entry is None:
            step_result = ChainStepResult(
                entry_id=step.entry_id,
                success=False,
                error=f"entry '{step.entry_id}' not found in store",
            )
            result.steps.append(step_result)
            if step.stop_on_error:
                break
            continue

        try:
            response = replay_request(entry, override_host=step.override_host)
            step_result = ChainStepResult(
                entry_id=step.entry_id,
                success=True,
                status_code=response.status_code,
            )
        except ReplayError as exc:
            step_result = ChainStepResult(
                entry_id=step.entry_id,
                success=False,
                error=str(exc),
            )
            result.steps.append(step_result)
            if step.stop_on_error:
                break
            continue

        result.steps.append(step_result)

    return result
