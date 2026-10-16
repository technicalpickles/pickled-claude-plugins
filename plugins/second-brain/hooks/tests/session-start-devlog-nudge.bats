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

@test "stays silent when devlog_mode is sidechain" {
  CLAUDE_PLUGIN_OPTION_DEVLOG_MODE=sidechain run bash "$HOOK"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "still nudges when devlog_mode is nudge, both, or unset" {
  for mode in nudge both; do
    CLAUDE_PLUGIN_OPTION_DEVLOG_MODE=$mode run bash "$HOOK"
    [ "$status" -eq 0 ]
    echo "$output" | jq -e '.hookSpecificOutput.hookEventName == "SessionStart"'
  done

  run env -u CLAUDE_PLUGIN_OPTION_DEVLOG_MODE bash "$HOOK"
  echo "$output" | jq -e '.hookSpecificOutput.hookEventName == "SessionStart"'
}
