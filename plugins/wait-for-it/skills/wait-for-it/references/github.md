# GitHub probes

## PR checks settling

Use the shipped script — do not hand-roll a "count of non-pending checks"
probe. An earlier version of this recipe did exactly that and broke on a
real PR (2026-08-28): retriggering CI grew the
total check count mid-watch (11 -> 15, as reruns and a security recheck got
added), which silently invalidates any probe that assumes a fixed total.

    ../probes/github-checks-settled.sh <OWNER>/<REPO> <NUM>

Prints the sorted, comma-joined names of checks still pending, e.g.
`pending:Fresh Eyes Review,buildkite/claude-code`. Terminal state is the
empty tail: `pending:`. It never needs to know a total, so a growing or
shrinking check count can't invalidate it.

Wrap it in the loop as usual:

    watch-loop.sh --label 'pr-<NUM>-checks' --interval 30 \
      --probe '<skill-dir>/probes/github-checks-settled.sh <OWNER>/<REPO> <NUM>'

## Which checks landed, not just how many

When the user wants the name of each check as it lands, emit the sorted set of
settled checks and let `watch-loop.sh` diff it:

    gh pr checks <NUM> --repo <OWNER>/<REPO> --json name,bucket \
      | jq -r '[.[] | select(.bucket != "pending") | "\(.name):\(.bucket)"] | sort | join(",")'

## Actions run finishing

    gh run list --repo <OWNER>/<REPO> --limit 1 --json status,conclusion \
      | jq -r '.[0] | "\(.status)/\(.conclusion)"'

`conclusion` has more values than just success/failure (`skipped`, `timed_out`,
`action_required`, `neutral`, `stale`, `startup_failure` all exist too) — do
not filter to success only; treat any change in the emitted string as the run
landing.

## Notes

- Interval 30s or more. `gh` counts against the GitHub API rate limit.
- If the project already has a cached PR-state register (an out-of-band
  poller), check it before arming a new watch.
