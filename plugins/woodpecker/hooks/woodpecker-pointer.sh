#!/usr/bin/env bash
# Points Claude at the woodpecker skills, a backstop for when description
# matching alone misses them (pirpg#68 never loaded either skill).
#
# PostToolUse only, once per session. SessionStart is not used: sessions often
# start in a parent directory and `cd` into the repo, which SessionStart never
# sees. The PostToolUse payload's cwd follows a Bash `cd`, so the first tool
# call after entering a Woodpecker repo points. Fires when:
#   - the cwd, or a directory above it, has a Woodpecker config; or
#   - the tool call's input or output mentions Woodpecker, which covers
#     working on another repo's pipeline without a `cd` (`gh --repo`, a Read).

payload=$(cat)

field() {
  printf '%s' "$payload" | jq -r "$1 // empty" 2>/dev/null
}

config_present() {
  local dir=$1
  while :; do
    [ -f "$dir/.woodpecker.yml" ] || [ -f "$dir/.woodpecker.yaml" ] || [ -d "$dir/.woodpecker" ] && return 0
    [ "$dir" = "/" ] || [ -z "$dir" ] && return 1
    dir=$(dirname "$dir")
  done
}

emit() { # emit <lead sentence>
  local context="$1 To find out what a pipeline did (whether it ran, which step failed, why a pull_request pipeline never showed up, whether a new step or secret works), use the woodpecker:woodpecker-investigating-pipelines skill before reading pipeline, status or webhook state by hand. To write or change a Woodpecker config, including how a step gets a secret (from_secret, secret filters), use woodpecker:woodpecker-authoring-pipelines."
  jq -n --arg context "$context" '{
    hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $context}
  }'
}

[ "$(field .hook_event_name)" = "PostToolUse" ] || exit 0

session=$(field .session_id | tr -cd 'A-Za-z0-9_-')
[ -n "$session" ] || exit 0
marker="${TMPDIR:-/tmp}/woodpecker-plugin-pointer/$session"
[ -e "$marker" ] && exit 0

cwd=$(field .cwd)
cwd=${cwd:-${CLAUDE_PROJECT_DIR:-$PWD}}

if config_present "$cwd"; then
  lead="This project builds with Woodpecker CI."
elif printf '%s' "$payload" | jq -r '[.tool_input, .tool_response] | tostring' 2>/dev/null |
  grep -Eq '\.woodpecker(\.ya?ml|/)|ci/woodpecker/|woodpecker-cli|/repos/[0-9]+/pipeline/[0-9]+'; then
  lead="That tool call touched Woodpecker CI."
else
  exit 0
fi

mkdir -p "$(dirname "$marker")" && touch "$marker"
emit "$lead"
