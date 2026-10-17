"""woodpecker-snapshot CLI entry point."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional, Sequence

from . import formatter, refs, states
from .cli import Pipeline, WoodpeckerCli, WpError

LIST_LIMIT = 100


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="woodpecker-snapshot",
        description="Snapshot a Woodpecker pipeline: state, step states, and the first failed step's log tail.",
    )
    parser.add_argument(
        "ref",
        nargs="?",
        help="Pipeline number or a Woodpecker pipeline URL (.../repos/<id>/pipeline/<n>). "
        "If omitted, finds the pipeline for the current commit (or --sha / --pr).",
    )
    parser.add_argument("--repo", help="owner/name (default: from the git remote)")
    parser.add_argument("--sha", help="commit SHA, full or short (default: HEAD)")
    parser.add_argument("--pr", type=int, help="use this GitHub PR's head commit")
    parser.add_argument("--tail", type=int, default=50, help="log lines to show for the failed step (default: 50)")
    return parser.parse_args(argv)


def _find_for_sha(pipelines: List[Pipeline], sha: str) -> Optional[Pipeline]:
    matches = [p for p in pipelines if refs.sha_matches(p.commit, sha)]
    return max(matches, key=lambda p: p.number) if matches else None


def main(argv: Optional[Sequence[str]] = None, client: Optional[WoodpeckerCli] = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    client = client or WoodpeckerCli()

    repo = args.repo
    number: Optional[int] = None
    url = refs.parse_pipeline_url(args.ref) if args.ref else None
    if url:
        repo, number = url.repo, url.number
    elif args.ref:
        if not args.ref.isdigit():
            print("error: REF must be a pipeline number or a Woodpecker pipeline URL, got %r" % args.ref, file=sys.stderr)
            return 2
        number = int(args.ref)

    repo = repo or refs.repo_from_git()
    if not repo:
        print("error: could not work out the repo from the git remote; pass --repo owner/name", file=sys.stderr)
        return 2

    sha = None
    if number is None:
        sha = args.sha or (refs.pr_head_sha(args.pr) if args.pr else refs.head_sha())
        if not sha:
            print("error: could not work out a commit; pass --sha or --pr", file=sys.stderr)
            return 2

    try:
        pipelines = client.pipelines(repo, limit=LIST_LIMIT)
        if number is None:
            found = _find_for_sha(pipelines, sha)
            if found is None:
                sys.stdout.write(formatter.format_no_pipeline(repo, sha, pipelines))
                return 0
            pipeline = found
        else:
            pipeline = next((p for p in pipelines if p.number == number), Pipeline(number, "", "", "", ""))

        steps = client.steps(repo, pipeline.number)
        assessment = states.assess(pipeline.status, steps)
        log = None
        if assessment.state == states.FAILED and assessment.first_failed is not None:
            log = client.log(repo, pipeline.number, assessment.first_failed.name)
    except WpError as err:
        sys.stdout.write(formatter.format_problem(err, repo))
        return 2

    sys.stdout.write(formatter.format_pipeline(repo, pipeline, steps, assessment, log, args.tail))
    return 0


if __name__ == "__main__":
    sys.exit(main())
