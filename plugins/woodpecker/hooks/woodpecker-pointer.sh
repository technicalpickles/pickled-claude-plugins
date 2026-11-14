#!/usr/bin/env bash
# Points Claude at the woodpecker skills, which description matching alone
# triggers on 1-5 of 10 relevant prompts (skills/*/evals).
#
# SessionStart: when the working directory, or a directory above it, has a
#   Woodpecker config.
# PostToolUse: the first time in a session that a tool call's input or output
#   mentions Woodpecker. Sessions often work on a Woodpecker repo from somewhere
#   else (`cd` into it, `gh --repo`), so a cwd check alone misses them. Silent
#   when the cwd has a config, since SessionStart already pointed.

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

emit() { # emit <event> <lead sentence>
  local context="$2 To find out what a pipeline did (whether it ran, which step failed, why a pull_request pipeline never showed up, whether a new step or secret works), use the woodpecker:woodpecker-investigating-pipelines skill before reading pipeline, status or webhook state by hand. To write or change a Woodpecker config, including how a step gets a secret (from_secret, secret filters), use woodpecker:woodpecker-authoring-pipelines."
  jq -n --arg event "$1" --arg context "$context" '{
    hookSpecificOutput: {hookEventName: $event, additionalContext: $context}
  }'
}

cwd=$(field .cwd)
cwd=${cwd:-${CLAUDE_PROJECT_DIR:-$PWD}}

case "$(field .hook_event_name)" in
  SessionStart)
    config_present "$cwd" || exit 0
    emit SessionStart "This project builds with Woodpecker CI."
    ;;
  PostToolUse)
    config_present "$cwd" && exit 0

    session=$(field .session_id | tr -cd 'A-Za-z0-9_-')
    [ -n "$session" ] || exit 0
    marker="${TMPDIR:-/tmp}/woodpecker-plugin-pointer/$session"
    [ -e "$marker" ] && exit 0

    printf '%s' "$payload" | jq -r '[.tool_input, .tool_response] | tostring' 2>/dev/null |
      grep -Eq '\.woodpecker(\.ya?ml|/)|ci/woodpecker/|woodpecker-cli|/repos/[0-9]+/pipeline/[0-9]+' || exit 0

    mkdir -p "$(dirname "$marker")" && touch "$marker"
    emit PostToolUse "That tool call touched Woodpecker CI."
    ;;
esac
exit 0
