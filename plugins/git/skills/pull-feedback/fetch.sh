#!/usr/bin/env bash
set -euo pipefail

# fetch.sh - Pull PR review feedback into a triaged working doc.
#
# Usage:
#   fetch.sh <pr-ref>                     # fetch from GitHub, write doc
#   fetch.sh --render-only \              # render only from local JSON
#     --graphql <file> --comments <file>

require_gh_auth() {
  if ! gh auth status >/dev/null 2>&1; then
    echo "error: gh is not authenticated" >&2
    echo "run: gh auth login" >&2
    exit 1
  fi
}

RENDER_ONLY=0
GRAPHQL_FILE=""
COMMENTS_FILE=""
REF=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --render-only) RENDER_ONLY=1; shift ;;
    --graphql) GRAPHQL_FILE="$2"; shift 2 ;;
    --comments) COMMENTS_FILE="$2"; shift 2 ;;
    --) shift; REF="${1:-}"; break ;;
    -*) echo "unknown flag: $1" >&2; exit 1 ;;
    *) REF="$1"; shift ;;
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
    echo
    echo "_No unresolved threads._"
    return
  fi

  echo "$pr" | jq -r '
    [.reviewThreads.nodes[] | select(.isResolved == false)]
    | sort_by(.path, (.line // .originalLine))
    | to_entries[]
    | "\(.key + 1)\t\(.value.id)\t\(.value.path)\t\(.value.line // .value.originalLine)\t\(.value.comments.nodes[0].author.login)\t\(.value.isOutdated)"
  ' | while IFS=$'\t' read -r idx thread_id path line first_author outdated; do
    echo
    local suffix=""
    [[ "$outdated" == "true" ]] && suffix=" ⚠️ outdated"
    echo "### \`$path:$line\` — @$first_author$suffix"
    echo "<!-- thread: $idx, id: $thread_id -->"
    echo "**Verdict (tentative):** _pending triage_"
    echo

    # Render the comment chain as a single blockquote
    echo "$pr" | jq -r \
      --arg tid "$thread_id" \
      '
        .reviewThreads.nodes[]
        | select(.id == $tid)
        | .comments.nodes
        | map("> @\(.author.login): \(.body)")
        | join("\n>\n")
      '

    echo
    echo "**Reasoning:** _pending triage_"
    echo "**Plan:** _pending triage_"

    if [[ "$idx" -lt "$thread_count" ]]; then
      echo
      echo "---"
    fi
  done

  local comment_count
  comment_count="$(jq 'length' "$comments")"
  if [[ "$comment_count" -gt 0 ]]; then
    echo
    echo "## General comments"
    echo
    jq -r '.[] | "- @\(.user.login): \"\(.body)\""' "$comments"
  fi
}

resolve_pr() {
  local ref="${1:-}"

  if [[ -z "$ref" ]]; then
    # Auto-detect from current branch
    if ! gh pr view --json number,url,headRepositoryOwner,headRepository 2>/dev/null; then
      echo "error: no PR found for current branch" >&2
      echo "pass a PR ref explicitly (e.g., 123, #123, owner/repo#123, or a PR URL)" >&2
      exit 1
    fi
    return
  fi

  # Strip URL prefix, handle org/repo#N, #N, bare number
  case "$ref" in
    https://github.com/*/pull/*)
      gh pr view "$ref" --json number,url,headRepositoryOwner,headRepository
      ;;
    *#*)
      local repo="${ref%#*}"
      local number="${ref#*#}"
      gh pr view "$number" --repo "$repo" --json number,url,headRepositoryOwner,headRepository
      ;;
    '#'*)
      gh pr view "${ref#\#}" --json number,url,headRepositoryOwner,headRepository
      ;;
    *)
      gh pr view "$ref" --json number,url,headRepositoryOwner,headRepository
      ;;
  esac
}

live_fetch() {
  require_gh_auth
  local ref="${1:-}"

  local pr_json
  pr_json="$(resolve_pr "$ref")"

  local owner repo number url
  owner="$(echo "$pr_json" | jq -r '.headRepositoryOwner.login')"
  repo="$(echo "$pr_json" | jq -r '.headRepository.name')"
  number="$(echo "$pr_json" | jq -r '.number')"
  url="$(echo "$pr_json" | jq -r '.url')"

  local graphql_file comments_file
  graphql_file="$(mktemp)"
  comments_file="$(mktemp)"
  trap 'rm -f "$graphql_file" "$comments_file"' EXIT

  local query_path
  query_path="$(dirname "${BASH_SOURCE[0]}")/lib/query.graphql"

  gh api graphql \
    -F owner="$owner" \
    -F repo="$repo" \
    -F number="$number" \
    -f query="$(cat "$query_path")" \
    > "$graphql_file"

  gh api "repos/$owner/$repo/issues/$number/comments" > "$comments_file"

  local out_dir=".scratch/pr-reviews/$number"
  mkdir -p "$out_dir"
  local out_file="$out_dir/threads.md"

  render "$graphql_file" "$comments_file" > "$out_file"

  local thread_count
  thread_count="$(jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)] | length' "$graphql_file")"

  local outdated_count
  outdated_count="$(jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false and .isOutdated == true)] | length' "$graphql_file")"

  local reviewers
  reviewers="$(jq -r '
    .data.repository.pullRequest.latestReviews.nodes
    | if length == 0 then "(none)"
      else map("@\(.author.login) (\(.state))") | join(", ")
      end
  ' "$graphql_file")"

  echo "wrote: $out_file"
  echo "threads: $thread_count unresolved ($outdated_count outdated)"
  echo "reviewers: $reviewers"
}

if [[ "$RENDER_ONLY" -eq 1 ]]; then
  [[ -n "$GRAPHQL_FILE" && -n "$COMMENTS_FILE" ]] || {
    echo "--render-only requires --graphql and --comments" >&2
    exit 1
  }
  render "$GRAPHQL_FILE" "$COMMENTS_FILE"
  exit 0
fi

live_fetch "${REF:-}"
