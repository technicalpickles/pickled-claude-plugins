#!/usr/bin/env bats
# Tests for the SessionStart hook that nudges devlog usage.

HOOK="$BATS_TEST_DIRNAME/../session-start-devlog-nudge.sh"

@test "emits valid SessionStart hookSpecificOutput JSON" {
  run bash "$HOOK"

  [ "$status" -eq 0 ]
  echo "$output" | jq -e '.hookSpecificOutput.hookEventName == "SessionStart"'
}

@test "additionalContext mentions the devlog skill and when to use it" {
  run bash "$HOOK"

  context=$(echo "$output" | jq -r '.hookSpecificOutput.additionalContext')

  [[ "$context" == *"second-brain:devlog"* ]]
  [[ "$context" == *"don't ask"* ]]
}

@test "additionalContext calls out what devlog is NOT for" {
  run bash "$HOOK"

  context=$(echo "$output" | jq -r '.hookSpecificOutput.additionalContext')

  [[ "$context" == *"process-inbox"* ]]
  [[ "$context" == *"second-brain:capture"* ]]
}
