#!/usr/bin/env bash
set -euo pipefail

# fetch.sh - Pull PR review feedback into a triaged working doc.
#
# Usage:
#   fetch.sh <pr-ref>                     # fetch from GitHub, write doc
#   fetch.sh --render-only \              # render only from local JSON
#     --graphql <file> --comments <file>

RENDER_ONLY=0
GRAPHQL_FILE=""
COMMENTS_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --render-only) RENDER_ONLY=1; shift ;;
    --graphql) GRAPHQL_FILE="$2"; shift 2 ;;
    --comments) COMMENTS_FILE="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done

render() {
  local graphql="$1"
  local comments="$2"

  local pr
  pr="$(jq '.data.repository.pullRequest' "$graphql")"

  local number title url state
  number="$(echo "$pr" | jq -r '.number')"
  title="$(echo "$pr" | jq -r '.title')"
  url="$(echo "$pr" | jq -r '.url')"
  state="$(echo "$pr" | jq -r '.state' | tr '[:upper:]' '[:lower:]')"

  local decision
  decision="$(echo "$pr" | jq -r '.reviewDecision // empty' | tr '[:upper:]' '[:lower:]' | tr '_' '-')"

  local status="$state"
  [[ -n "$decision" ]] && status="$state, $decision"

  local reviewers
  reviewers="$(echo "$pr" | jq -r '
    .latestReviews.nodes
    | if length == 0 then "(none)"
      else map("@\(.author.login) (\(.state | ascii_downcase | gsub("_"; " ")))") | join(", ")
      end
  ')"

  local thread_count
  thread_count="$(echo "$pr" | jq '[.reviewThreads.nodes[] | select(.isResolved == false)] | length')"

  cat <<EOF
# PR #$number: $title

**URL:** $url
**Status:** $status
**Reviewers:** $reviewers

## Threads ($thread_count unresolved)

EOF

  if [[ "$thread_count" -eq 0 ]]; then
    echo "_No unresolved threads._"
  fi
}

if [[ "$RENDER_ONLY" -eq 1 ]]; then
  [[ -n "$GRAPHQL_FILE" && -n "$COMMENTS_FILE" ]] || {
    echo "--render-only requires --graphql and --comments" >&2
    exit 1
  }
  render "$GRAPHQL_FILE" "$COMMENTS_FILE"
  exit 0
fi

echo "live mode not yet implemented" >&2
exit 1
