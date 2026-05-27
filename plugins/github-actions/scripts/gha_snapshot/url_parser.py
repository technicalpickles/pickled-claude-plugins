"""Parse GitHub Actions run URLs into structured RunRef objects."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Matches URLs like:
#   https://github.com/<owner>/<repo>/actions/runs/<run_id>[/...]
_RUN_URL = re.compile(
    r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/actions/runs/(?P<run_id>\d+)"
)


@dataclass(frozen=True)
class RunRef:
    owner: str
    repo: str
    run_id: int

    @property
    def repo_slug(self) -> str:
        return f"{self.owner}/{self.repo}"


def parse_run_url(url: str) -> RunRef:
    """Parse a GitHub Actions run URL.

    Accepts canonical URLs, URLs with trailing slashes, and URLs with extra
    path segments like `/job/<id>` or `/attempts/<n>`.

    Raises ValueError if the URL doesn't point at a GHA run.
    """
    match = _RUN_URL.match(url.strip())
    if not match:
        raise ValueError(f"not a GitHub Actions run URL: {url!r}")
    return RunRef(
        owner=match["owner"],
        repo=match["repo"],
        run_id=int(match["run_id"]),
    )
