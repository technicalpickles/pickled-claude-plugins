"""Render a run-view JSON + log text into a human-readable snapshot block."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from .url_parser import RunRef

_ICONS = {
    "success": "✓",
    "failure": "✗",
    "cancelled": "⊘",
    "skipped": "⊘",
    "neutral": "·",
    "timed_out": "✗",
    "action_required": "!",
}
_DEFAULT_ICON = "…"

# `gh run view --log-failed` emits lines like:
#   <job-name>\t<step-name>\t<line>
_LOG_LINE = re.compile(r"^(?P<job>[^\t]+)\t(?P<step>[^\t]+)\t(?P<content>.*)$")
_ANNOTATION = re.compile(r"::(error|warning|notice)[^:]*::.+")


def format_snapshot(run: dict[str, Any], log_failed: str, ref: RunRef, *, tail: int) -> str:
    sections = [
        _format_header(run),
        _format_jobs(run),
        _format_failed_steps(run, log_failed, tail),
        _format_annotations(log_failed),
        _format_links(run, ref),
    ]
    return "\n\n".join(s for s in sections if s)


def _format_header(run: dict[str, Any]) -> str:
    duration = _duration(run.get("createdAt"), run.get("updatedAt"))
    sha = (run.get("headSha") or "")[:7]
    lines = [
        f"Run: {run.get('workflowName', '?')} #{run.get('number', '?')}",
        f"Status: {run.get('conclusion') or run.get('status', '?')} ({duration})",
        f"Trigger: {run.get('event', '?')} on {run.get('headBranch', '?')} @ {sha}",
        f"URL: {run.get('url', '?')}",
    ]
    return "\n".join(lines)


def _format_jobs(run: dict[str, Any]) -> str:
    out = ["Jobs:"]
    for job in run.get("jobs", []):
        icon = _ICONS.get(job.get("conclusion") or "", _DEFAULT_ICON)
        duration = _duration(job.get("startedAt"), job.get("completedAt"))
        line = f"  {icon} {job['name']} ({duration})"
        if job.get("conclusion") == "failure":
            failed_step = _first_failed_step(job)
            if failed_step:
                line += f' — failed at step "{failed_step["name"]}"'
        elif job.get("conclusion") == "skipped":
            line += " (skipped — dependency failed)"
        out.append(line)
    return "\n".join(out)


def _format_failed_steps(run: dict[str, Any], log_failed: str, tail: int) -> str:
    failed_jobs = [j for j in run.get("jobs", []) if j.get("conclusion") == "failure"]
    if not failed_jobs:
        return ""
    blocks = []
    for job in failed_jobs:
        step = _first_failed_step(job)
        if not step:
            continue
        relevant = _log_lines_for(log_failed, job["name"], step["name"], tail)
        if not relevant:
            continue
        blocks.append(
            f'Failed step output ({job["name"]} → "{step["name"]}", last {len(relevant)} lines):\n'
            + "\n".join(f"  {line}" for line in relevant)
        )
    return "\n\n".join(blocks)


def _format_annotations(log_failed: str) -> str:
    by_job: dict[str, list[str]] = {}
    for line in log_failed.splitlines():
        m = _LOG_LINE.match(line)
        if not m:
            continue
        if _ANNOTATION.search(m["content"]):
            by_job.setdefault(m["job"], []).append(m["content"].strip())
    if not by_job:
        return ""
    out = ["Annotations:"]
    for job_name, anns in by_job.items():
        for ann in anns:
            out.append(f"  {job_name}: {ann}")
    return "\n".join(out)


def _format_links(run: dict[str, Any], ref: RunRef) -> str:
    out = ["Links:", f"  Run:  {run.get('url', '?')}"]
    for job in run.get("jobs", []):
        if job.get("conclusion") == "failure":
            out.append(f"  {job['name']}: {job.get('url', '?')}")
    return "\n".join(out)


def _first_failed_step(job: dict[str, Any]) -> dict[str, Any] | None:
    for step in job.get("steps", []):
        if step.get("conclusion") == "failure":
            return step
    return None


def _log_lines_for(log: str, job_name: str, step_name: str, tail: int) -> list[str]:
    """Extract log lines for a given job + step.

    `gh run view --log-failed` sometimes emits "UNKNOWN STEP" in the step
    column when the runner couldn't resolve a display name (common on
    short-lived steps). When step-name matching yields nothing, fall back
    to all lines for the job, then trim everything after the last
    `##[error]` marker so post-step cleanup output doesn't drown the
    actual failure context.
    """
    job_matches = []
    step_matches = []
    for line in log.splitlines():
        m = _LOG_LINE.match(line)
        if not m or m["job"] != job_name:
            continue
        job_matches.append(m["content"])
        if m["step"] == step_name:
            step_matches.append(m["content"])
    if step_matches:
        return step_matches[-tail:]
    last_error = _last_index(job_matches, "##[error]")
    if last_error is not None:
        job_matches = job_matches[: last_error + 1]
    return job_matches[-tail:]


def _last_index(lines: list[str], needle: str) -> int | None:
    for i in range(len(lines) - 1, -1, -1):
        if needle in lines[i]:
            return i
    return None


def _duration(start: str | None, end: str | None) -> str:
    if not start or not end:
        return "—"
    try:
        s = datetime.fromisoformat(start.replace("Z", "+00:00")).astimezone(timezone.utc)
        e = datetime.fromisoformat(end.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return "—"
    seconds = int((e - s).total_seconds())
    if seconds < 60:
        return f"{seconds}s"
    return f"{seconds // 60}m {seconds % 60:02d}s"
