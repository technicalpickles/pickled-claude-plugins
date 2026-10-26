#!/usr/bin/env bats

HOOK="$BATS_TEST_DIRNAME/../hooks/inject-session-context.py"
PARK='{"tool_input":{"skill":"agent-meta:park"},"session_id":"sid-123","transcript_path":"/tmp/t.jsonl"}'

run_hook() {
  run env -i PATH="$PATH" "$@" python3 "$HOOK" <<<"$PAYLOAD"
}

context() {
  python3 -c 'import json,sys; print(json.load(sys.stdin)["hookSpecificOutput"]["additionalContext"])' <<<"$output"
}

@test "injects the literal destination for park" {
  PAYLOAD=$PARK run_hook AGENT_PARK_DESTINATION='sb file {file}'
  [ "$status" -eq 0 ]
  [ "$(context)" = "Park destination: sb file {file}" ]
}

@test "does not inject the session ID or transcript" {
  PAYLOAD=$PARK run_hook AGENT_PARK_DESTINATION='sb file {file}'
  [[ "$output" != *sid-123* ]]
  [[ "$output" != *t.jsonl* ]]
}

@test "prints nothing for park when no destination is configured" {
  PAYLOAD=$PARK run_hook
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "prints nothing for other skills" {
  PAYLOAD='{"tool_input":{"skill":"git:commit"}}' run_hook AGENT_PARK_DESTINATION='sb file {file}'
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "helper output wins over the literal destination" {
  PAYLOAD=$PARK run_hook AGENT_PARK_DESTINATION='literal {file}' AGENT_PARK_DESTINATION_HELPER='echo helper {file}'
  [ "$(context)" = "Park destination: helper {file}" ]
}

@test "falls back to the literal destination when the helper fails" {
  PAYLOAD=$PARK run_hook AGENT_PARK_DESTINATION='literal {file}' AGENT_PARK_DESTINATION_HELPER='exit 1'
  [ "$(context)" = "Park destination: literal {file}" ]
}

@test "rejects a multi-line helper template" {
  PAYLOAD=$PARK run_hook AGENT_PARK_DESTINATION_HELPER='printf "a\nb"'
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "exits quietly on malformed input" {
  PAYLOAD='not json' run_hook AGENT_PARK_DESTINATION='sb file {file}'
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}
