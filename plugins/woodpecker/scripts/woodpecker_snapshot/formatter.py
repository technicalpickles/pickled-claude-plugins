"""Render a snapshot as plain text. The first line is always `State: <state>`."""

from __future__ import annotations

from typing import List, Optional

from . import states
from .cli import ANSI_RE, Pipeline, Step, WpError

_STATE_HINTS = {
    states.QUEUED: "Waiting for an agent. Normal when the server's concurrency limit is low; not a failure.",
    states.BLOCKED: "Waiting for manual approval in the Woodpecker UI (common for pull requests from forks).",
}


def _short(sha: str) -> str:
    return sha[:7] if sha else "?"


def clean_tail(log: str, tail: int) -> List[str]:
    lines = [ANSI_RE.sub("", line).rstrip() for line in log.replace("\r", "").splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    return lines[-tail:] if tail > 0 else []


def format_pipeline(
    repo: str,
    pipeline: Pipeline,
    steps: List[Step],
    assessment: states.Assessment,
    log: Optional[str],
    tail: int,
) -> str:
    out = ["State: %s" % assessment.state]
    if assessment.detail:
        out.append("Detail: %s" % assessment.detail)
    if assessment.state in _STATE_HINTS:
        out.append("Detail: %s" % _STATE_HINTS[assessment.state])
    out.append("Repo: %s" % repo)
    if pipeline.status:
        where = ", ".join(x for x in (pipeline.branch, pipeline.event) if x)
        commit = ", commit %s" % _short(pipeline.commit) if pipeline.commit else ""
        out.append("Pipeline: #%d (status %s)%s%s" % (pipeline.number, pipeline.status, " on " + where if where else "", commit))
    else:
        out.append("Pipeline: #%d (status not in the recent list, state taken from its steps)" % pipeline.number)

    if steps:
        out += ["", "Steps:"]
        for step in steps:
            mark = "  <- first failure" if step is assessment.first_failed else ""
            out.append("  %s/%s: %s%s" % (step.workflow, step.name, step.state, mark))
    if assessment.skipped_after:
        out.append("(%d later steps skipped after the first failure.)" % assessment.skipped_after)

    if assessment.state == states.PASSED and assessment.ignored_failures:
        names = ", ".join(s.name for s in assessment.ignored_failures)
        out.append("Warning: failed but ignored by the pipeline (likely `failure: ignore`): %s" % names)
    if assessment.state == states.RUNNING:
        out.append("The pipeline is still running, so step states and any logs are partial.")

    if log is not None and assessment.first_failed is not None:
        lines = clean_tail(log, tail)
        out += ["", "Log tail (%s, last %d lines):" % (assessment.first_failed.name, len(lines)), "```"]
        out += lines
        out.append("```")
    return "\n".join(out) + "\n"


def format_no_pipeline(repo: str, sha: str, recent: List[Pipeline]) -> str:
    out = [
        "State: no pipeline",
        "Repo: %s" % repo,
        "Commit: %s" % _short(sha),
        "No pipeline in the newest %d for this repo matches that commit. This never means passing." % max(len(recent), 0)
        if recent
        else "The server has no pipelines at all for this repo. This never means passing.",
        "",
        "Likely causes:",
        "  - the webhook was not delivered (Woodpecker server or its tunnel down, forge misconfigured)",
        "  - the repo is not activated on the Woodpecker server",
        "  - the pipeline's `when:` rules filtered the event out",
        "  - an old pipeline was removed from the server",
        "  - the commit has not been pushed yet",
    ]
    if recent:
        out += ["", "Newest pipelines:"]
        for p in recent[:5]:
            out.append("  #%d %s %s %s" % (p.number, p.status, p.branch, _short(p.commit)))
    return "\n".join(out) + "\n"


def format_problem(err: WpError, repo: Optional[str]) -> str:
    kind = err.kind
    if kind == WpError.NOT_INSTALLED:
        state, lines = states.NOT_SET_UP, [
            "woodpecker-cli is not on PATH.",
            'Pin it in mise.toml: "aqua:woodpecker-ci/woodpecker/woodpecker-cli" = "<server version>" (or brew install woodpecker-cli).',
            "Then log in once with `woodpecker-cli setup --server <url>`. Details: references/setup.md",
        ]
    elif kind == WpError.NOT_CONFIGURED:
        state, lines = states.NOT_SET_UP, [
            "woodpecker-cli has no saved login.",
            "Run once, outside the command sandbox (it writes the Keychain): woodpecker-cli setup --server <url>",
            "The browser step needs Chrome or Firefox; Safari blocks it. Details: references/setup.md",
        ]
    elif kind == WpError.UNAUTHORIZED:
        state, lines = states.UNAUTHORIZED, [
            "The server rejected the saved token (401/403). It may be expired or revoked.",
            "Run `woodpecker-cli setup --server <url>` again, outside the command sandbox.",
        ]
    elif kind == WpError.NETWORK_DENIED:
        state, lines = states.UNREACHABLE, [
            "The command sandbox blocked the connection to the Woodpecker host.",
            "Add the host to the sandbox's network allowlist (allowed_domains) and retry. This says nothing about the code.",
        ]
    elif kind == WpError.UNREACHABLE:
        state, lines = states.UNREACHABLE, [
            "Could not reach the Woodpecker server (down, tunnel down, or no network).",
            "This says nothing about the code. If pushes are not producing builds, suspect the same cause.",
        ]
    elif kind == WpError.NOT_FOUND:
        state, lines = states.UNKNOWN, [
            "Woodpecker answered 404%s: the repo is not activated on the server, the name is wrong, or the saved login cannot see it."
            % (" for %s" % repo if repo else ""),
        ]
    else:
        state, lines = states.UNKNOWN, ["woodpecker-cli failed in a way this helper does not recognize."]
    out = ["State: %s" % state] + lines + ["Detail: %s" % err.message]
    return "\n".join(out) + "\n"
