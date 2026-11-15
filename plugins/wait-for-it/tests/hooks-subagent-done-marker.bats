#!/usr/bin/env bats
# Tests for the wait-for-it skill's shipped SubagentStop marker hook.
# No real Claude Code process involved -- feeds fake hook-input JSON on
# stdin, same shape SubagentStop actually delivers.

setup() {
  TEST_DIR="$(cd "$(dirname "$BATS_TEST_FILENAME")" && pwd)"
  SCRIPT="$TEST_DIR/../hooks/subagent-done-marker.sh"
  export TMPDIR="$(mktemp -d)"
}

teardown() {
  rm -rf "$TMPDIR"
}

@test "writes a marker file named after agent_id, containing the full input" {
  input='{"session_id":"abc123","hook_event_name":"SubagentStop","agent_id":"def456","agent_type":"Explore","last_assistant_message":"done"}'
  run bash -c "printf '%s' '$input' | '$SCRIPT'"
  [ "$status" -eq 0 ]

  marker="$TMPDIR/wait-for-it-subagent-done/def456.json"
  [ -f "$marker" ]
  run cat "$marker"
  [[ "$output" == *'"agent_id":"def456"'* ]]
  [[ "$output" == *'"last_assistant_message":"done"'* ]]
}

@test "exits 0 without writing a marker when agent_id is absent" {
  input='{"session_id":"abc123","hook_event_name":"Stop"}'
  run bash -c "printf '%s' '$input' | '$SCRIPT'"
  [ "$status" -eq 0 ]
  [ ! -d "$TMPDIR/wait-for-it-subagent-done" ]
}

@test "a second firing for a different agent_id does not clobber the first marker" {
  first='{"agent_id":"aaa111","hook_event_name":"SubagentStop"}'
  second='{"agent_id":"bbb222","hook_event_name":"SubagentStop"}'
  run bash -c "printf '%s' '$first' | '$SCRIPT'"
  [ "$status" -eq 0 ]
  run bash -c "printf '%s' '$second' | '$SCRIPT'"
  [ "$status" -eq 0 ]

  [ -f "$TMPDIR/wait-for-it-subagent-done/aaa111.json" ]
  [ -f "$TMPDIR/wait-for-it-subagent-done/bbb222.json" ]
}
