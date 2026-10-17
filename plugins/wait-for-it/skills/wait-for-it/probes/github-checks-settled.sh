#!/usr/bin/env bash
# Prints the sorted, comma-joined names of GitHub PR checks still pending.
# A probe for wait-for-it/watch-loop.sh -- terminal state is the empty tail
# ("pending:"). Never assumes a fixed total check count, unlike the retired
# "count of non-pending checks" recipe: a growing/shrinking total (reruns,
# new workflow runs appearing) can't invalidate this.
# See docs/superpowers/specs/2026-08-28-wait-for-it-probe-scripts-design.md
set -uo pipefail

if [ $# -ne 2 ]; then
  echo "github-checks-settled.sh: usage: github-checks-settled.sh <owner>/<repo> <pr-number>" >&2
  exit 2
fi

repo="$1"
num="$2"

checks_json="$(gh pr checks "$num" --repo "$repo" --json name,bucket 2>&1)"
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "github-checks-settled.sh: gh pr checks failed (rc=$rc): $checks_json" >&2
  exit "$rc"
fi

echo "$checks_json" \
  | jq -r '[.[] | select(.bucket == "pending") | .name] | sort | join(",") | "pending:\(.)"'
