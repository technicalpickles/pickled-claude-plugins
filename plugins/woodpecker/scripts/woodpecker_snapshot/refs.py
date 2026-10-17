"""Work out which repo and commit to look at, from args and the current git checkout."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from typing import Optional

_REMOTE_RE = re.compile(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?/?$")
_URL_RE = re.compile(r"/repos/(\d+)/pipeline/(\d+)(?:/\d+)?/?$")


@dataclass
class PipelineUrl:
    repo: str  # numeric repo ID; woodpecker-cli accepts it in place of owner/name
    number: int


def parse_remote(url: str) -> Optional[str]:
    """owner/name from the last two path segments of a git remote URL."""
    match = _REMOTE_RE.search(url.strip())
    return "%s/%s" % (match.group(1), match.group(2)) if match else None


def parse_pipeline_url(text: str) -> Optional[PipelineUrl]:
    match = _URL_RE.search(text.strip())
    return PipelineUrl(match.group(1), int(match.group(2))) if match else None


def sha_matches(full: str, given: str) -> bool:
    given = given.strip().lower()
    return bool(given) and full.lower().startswith(given)


def _git(args, cwd: Optional[str]) -> Optional[str]:
    try:
        out = subprocess.run(
            ["git"] + args, cwd=cwd, capture_output=True, text=True, timeout=15
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout.strip() if out.returncode == 0 and out.stdout.strip() else None


def repo_from_git(cwd: Optional[str] = None) -> Optional[str]:
    # Same order woodpecker-cli itself uses: upstream, then origin.
    for remote in ("upstream", "origin"):
        url = _git(["remote", "get-url", remote], cwd)
        if url:
            return parse_remote(url)
    return None


def head_sha(cwd: Optional[str] = None) -> Optional[str]:
    return _git(["rev-parse", "HEAD"], cwd)


def pr_head_sha(pr: int, cwd: Optional[str] = None) -> Optional[str]:
    try:
        out = subprocess.run(
            ["gh", "pr", "view", str(pr), "--json", "headRefOid", "-q", ".headRefOid"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout.strip() if out.returncode == 0 and out.stdout.strip() else None
