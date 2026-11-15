#!/usr/bin/env bash
# PostToolUse: inject `hk agent instructions --target claude-code` as context the
# first time a tool call runs inside a project that uses hk, once per session.
# Claude Code reports the working directory on every tool call and follows a Bash
# `cd`, so a session started in a parent directory picks the instructions up as soon
# as it works inside an hk repo. Shelling out at runtime (rather than copying the
# text) means the instructions track whatever hk version the project runs.

# shellcheck source=hk-common.sh
. "$(dirname "${BASH_SOURCE[0]}")/hk-common.sh"

payload=$(cat)

session=$(printf '%s' "$payload" | jq -r '.session_id // empty' 2>/dev/null | tr -c 'A-Za-z0-9_-' '_')
[ -n "$session" ] || exit 0
marker="${TMPDIR:-/tmp}/hk-instructions-$session"
[ ! -e "$marker" ] || exit 0

dir=$(hk_payload_dir "$payload")
hk_ready "$dir" || exit 0

instructions=$(cd "$dir" && hk agent instructions --target claude-code 2>/dev/null) || exit 0
[ -n "$instructions" ] || exit 0

: > "$marker"
jq -n --arg context "$instructions" '{
  hookSpecificOutput: {
    hookEventName: "PostToolUse",
    additionalContext: $context
  }
}'
