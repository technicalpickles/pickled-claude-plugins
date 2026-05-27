"""Turn user input into a RunRef.

Resolution priority:
  1. Explicit URL
  2. Explicit numeric run ID (with cwd's repo)
  3. PR number (most recent failed check)
  4. Default: latest failed run on current branch
"""

from __future__ import annotations

from typing import Optional

from .gh_client import GhClient
from .url_parser import RunRef, parse_run_url


class ResolveError(RuntimeError):
    """Raised when no run can be resolved from the inputs."""


def resolve(
    ref: Optional[str],
    *,
    pr: Optional[int] = None,
    client: Optional[GhClient] = None,
) -> RunRef:
    """Resolve a user-supplied ref into a RunRef.

    `ref` may be:
      - A full run URL → parsed directly
      - A numeric string → treated as a run_id, repo inferred from cwd
      - None → fall through to `pr` or default-branch lookup

    `pr` takes precedence over the default-branch lookup when `ref` is None.
    """
    client = client or GhClient()

    if ref:
        ref = ref.strip()
        if ref.startswith("http"):
            return parse_run_url(ref)
        if ref.isdigit():
            owner, repo = client.current_repo()
            return RunRef(owner=owner, repo=repo, run_id=int(ref))
        raise ResolveError(f"unrecognized ref: {ref!r}")

    if pr is not None:
        owner, repo = client.current_repo()
        checks = client.pr_checks(owner=owner, repo=repo, pr_number=pr)
        failures = [c for c in checks if c.get("state") == "FAILURE"]
        if not failures:
            raise ResolveError(f"no failed checks on PR #{pr}")
        # link looks like .../actions/runs/<id>/job/<job_id>
        return parse_run_url(failures[0]["link"])

    owner, repo = client.current_repo()
    branch = client.current_branch()
    runs = client.run_list_branch(owner=owner, repo=repo, branch=branch)
    if not runs:
        raise ResolveError(f"no failed runs on branch {branch!r}")
    return RunRef(owner=owner, repo=repo, run_id=int(runs[0]["databaseId"]))
