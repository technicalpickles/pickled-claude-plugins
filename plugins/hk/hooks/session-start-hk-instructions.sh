#!/usr/bin/env bash
# SessionStart: inject `hk agent instructions --target claude-code` as context,
# only in projects that use hk. Shelling out at runtime (rather than copying the
# text) means the instructions track whatever hk version the project runs.

# shellcheck source=hk-common.sh
. "$(dirname "${BASH_SOURCE[0]}")/hk-common.sh"

hk_ready || exit 0

instructions=$(cd "$(hk_project_dir)" && hk agent instructions --target claude-code 2>/dev/null) || exit 0
[ -n "$instructions" ] || exit 0

jq -n --arg context "$instructions" '{
  hookSpecificOutput: {
    hookEventName: "SessionStart",
    additionalContext: $context
  }
}'
