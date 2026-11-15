"""Turn a pipeline status plus its step states into one named state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .cli import Step

PASSED = "passed"
FAILED = "failed"
RUNNING = "running"
QUEUED = "queued"
BLOCKED = "blocked"
NO_PIPELINE = "no pipeline"
UNREACHABLE = "unreachable"
UNAUTHORIZED = "unauthorized"
NOT_SET_UP = "not set up"
UNKNOWN = "unknown"

# Pipeline statuses seen on a live server: success, failure, running, killed, canceled.
# The rest are expected from upstream but unseen, so anything not listed reports as
# UNKNOWN with the raw status, never a guess.
_STATUS_STATE = {
    "success": PASSED,
    "failure": FAILED,
    "error": FAILED,
    "killed": FAILED,
    "canceled": FAILED,
    "cancelled": FAILED,
    "running": RUNNING,
    "started": RUNNING,
    "pending": QUEUED,
    "blocked": BLOCKED,
}
_STOPPED = {"killed", "canceled", "cancelled"}
STEP_FAILED = {"failure", "error", "killed", "canceled", "cancelled"}
_STEP_NOT_RUN = {"skipped", "pending"}


@dataclass
class Assessment:
    state: str
    detail: str = ""
    first_failed: Optional[Step] = None
    ignored_failures: List[Step] = field(default_factory=list)
    skipped_after: int = 0


def _state_from_steps(steps: List[Step]) -> str:
    states = [s.state for s in steps]
    if any(s in STEP_FAILED for s in states):
        return FAILED
    if any(s == "running" for s in states):
        return RUNNING
    if states and all(s == "success" for s in states):
        return PASSED
    return UNKNOWN


def assess(status: Optional[str], steps: List[Step]) -> Assessment:
    raw = (status or "").lower()
    state = _STATUS_STATE.get(raw) if raw and raw != "unknown" else _state_from_steps(steps)
    if state is None:
        return Assessment(UNKNOWN, "pipeline status %r is not one this helper recognizes" % status)

    first_failed = next((s for s in steps if s.state in STEP_FAILED), None)
    result = Assessment(state, first_failed=first_failed)

    if state == FAILED:
        if raw in _STOPPED:
            result.detail = "stopped (status: %s), not necessarily a code failure" % raw
        if first_failed is None:
            result.detail = (
                result.detail + "; " if result.detail else ""
            ) + "no failed step found, so it failed before or outside any step (config error, clone failure)"
        else:
            idx = steps.index(first_failed)
            result.skipped_after = sum(1 for s in steps[idx + 1 :] if s.state in _STEP_NOT_RUN)
    elif state == PASSED:
        result.ignored_failures = [s for s in steps if s.state in STEP_FAILED]
    return result
