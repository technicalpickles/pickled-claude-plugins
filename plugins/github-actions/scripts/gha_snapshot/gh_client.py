"""Thin subprocess wrapper around the `gh` CLI.

Isolates all gh invocations so the rest of the code is testable against
captured JSON fixtures rather than live network calls.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any


class GhError(RuntimeError):
    """Raised when `gh` exits non-zero."""


_RUN_VIEW_FIELDS = (
    "conclusion,createdAt,databaseId,displayTitle,event,headBranch,"
    "headSha,jobs,name,number,startedAt,status,updatedAt,url,workflowName"
)


class GhClient:
    """Wraps `gh` CLI calls.

    Methods return parsed JSON (for `--json` calls) or raw stdout (for
    log calls). All methods raise GhError on non-zero exit, with stderr
    captured in the exception message.
    """

    def _run(self, args: list[str]) -> str:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise GhError(result.stderr.strip() or f"gh exited {result.returncode}")
        return result.stdout

    def run_view(self, *, owner: str, repo: str, run_id: int) -> dict[str, Any]:
        out = self._run([
            "gh", "run", "view", str(run_id),
            "--repo", f"{owner}/{repo}",
            "--json", _RUN_VIEW_FIELDS,
        ])
        return json.loads(out)

    def run_log_failed(self, *, owner: str, repo: str, run_id: int) -> str:
        return self._run([
            "gh", "run", "view", str(run_id),
            "--repo", f"{owner}/{repo}",
            "--log-failed",
        ])

    def run_list_branch(
        self, *, owner: str, repo: str, branch: str, status: str = "failure", limit: int = 1
    ) -> list[dict[str, Any]]:
        out = self._run([
            "gh", "run", "list",
            "--repo", f"{owner}/{repo}",
            "--branch", branch,
            "--status", status,
            "--limit", str(limit),
            "--json", "databaseId,conclusion,event,headBranch,headSha,name,startedAt,status,workflowName,url",
        ])
        return json.loads(out)

    def pr_checks(self, *, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        out = self._run([
            "gh", "pr", "checks", str(pr_number),
            "--repo", f"{owner}/{repo}",
            "--json", "name,state,link,workflow,bucket",
        ])
        return json.loads(out)

    def current_repo(self) -> tuple[str, str]:
        out = self._run([
            "gh", "repo", "view",
            "--json", "owner,name",
        ])
        data = json.loads(out)
        return data["owner"]["login"], data["name"]

    def current_branch(self) -> str:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            raise GhError(result.stderr.strip() or "git rev-parse failed")
        return result.stdout.strip()
