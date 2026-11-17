#!/usr/bin/env bash
# PostToolUse on Bash: after a `gh pr merge` lands, if the merged branch still has a
# worktree under `.claude/worktrees/`, tell the agent to remove it now. Firing at the
# merge is the point: a rule or skill that says "clean up after merge" is easy to skip,
# and this costs no context on any other tool call. Silent on anything unexpected.

payload=$(cat)

command=$(printf '%s' "$payload" | jq -r '.tool_input.command // empty' 2>/dev/null)
case "$command" in *"gh pr merge"*) ;; *) exit 0 ;; esac

dir=$(printf '%s' "$payload" | jq -r '.cwd // empty' 2>/dev/null)
dir=${dir:-${CLAUDE_PROJECT_DIR:-$PWD}}

# The words after `gh pr merge`, up to the end of that command.
rest=${command#*gh pr merge}
rest=$(printf '%s\n' "$rest" | head -n 1 | sed -e 's/&&.*//' -e 's/||.*//' -e 's/;.*//' -e 's/|.*//')

selector=""
repo=""
skip_next=""
set -f
# shellcheck disable=SC2086
set -- $rest
set +f
for word in "$@"; do
  if [ -n "$skip_next" ]; then
    [ "$skip_next" = repo ] && repo=$word
    skip_next=""
    continue
  fi
  case "$word" in
    -R | --repo) skip_next=repo ;;
    -t | --subject | -b | --body | -F | --body-file | --match-head-commit | -A | --author-email) skip_next=value ;;
    --repo=*) repo=${word#--repo=} ;;
    -*) ;;
    *) [ -z "$selector" ] && selector=$word ;;
  esac
done
selector=${selector//[\"\']/}
repo=${repo//[\"\']/}

set --
[ -n "$selector" ] && set -- "$selector"
[ -n "$repo" ] && set -- "$@" --repo "$repo"

pr=$(cd "$dir" 2>/dev/null && gh pr view "$@" --json state,headRefName,number 2>/dev/null) || exit 0
state=$(printf '%s' "$pr" | jq -r '.state // empty')
[ "$state" = MERGED ] || exit 0
branch=$(printf '%s' "$pr" | jq -r '.headRefName // empty')
number=$(printf '%s' "$pr" | jq -r '.number // empty')
[ -n "$branch" ] || exit 0

path=$(git -C "$dir" worktree list --porcelain 2>/dev/null | awk -v ref="refs/heads/$branch" '
  /^worktree / { path = substr($0, 10) }
  $0 == "branch " ref && path ~ /\/\.claude\/worktrees\// { print path; exit }
')
[ -n "$path" ] || exit 0

if command -v wt >/dev/null 2>&1; then
  remove="\`git fetch\`, then \`wt remove $branch -y\`"
else
  remove="\`git worktree remove $path\`"
fi

context="PR #$number ($branch) is merged, and its worktree is still at $path. Remove it now, from outside the worktree: $remove. Keep it only if the user said they're still using it or it is the root of a live session, and say which. Details are in the git-worktrees skill."

jq -n --arg context "$context" '{
  hookSpecificOutput: {
    hookEventName: "PostToolUse",
    additionalContext: $context
  }
}'
