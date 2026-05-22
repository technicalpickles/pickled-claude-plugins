"""gha-snapshot CLI entry point."""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from .formatter import format_snapshot
from .gh_client import GhClient, GhError
from .resolver import ResolveError, resolve


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="gha-snapshot",
        description="Snapshot a failing GitHub Actions run: metadata + failed-step log tail + annotations.",
    )
    parser.add_argument(
        "ref",
        nargs="?",
        help="Run URL or run ID. If omitted, uses --pr or latest failed run on current branch.",
    )
    parser.add_argument("--pr", type=int, help="Resolve via PR number (most recent failed check).")
    parser.add_argument(
        "--tail", type=int, default=50,
        help="Lines of failed-step log to include per failed job (default: 50).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    client = GhClient()

    try:
        run_ref = resolve(args.ref, pr=args.pr, client=client)
    except (ResolveError, GhError, ValueError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        run = client.run_view(owner=run_ref.owner, repo=run_ref.repo, run_id=run_ref.run_id)
        log = client.run_log_failed(
            owner=run_ref.owner, repo=run_ref.repo, run_id=run_ref.run_id
        )
    except GhError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(format_snapshot(run, log, run_ref, tail=args.tail))
    return 0


if __name__ == "__main__":
    sys.exit(main())
