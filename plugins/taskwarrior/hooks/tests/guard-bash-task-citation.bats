#!/usr/bin/env bats
# Tests for the PreToolUse:Bash hook guarding two risky bare-ID patterns:
# (1) mutating a task by its plain numeric ID, (2) citing a bare numeric ID
# in a git commit message.

HOOK="$BATS_TEST_DIRNAME/../guard-bash-task-citation.py"

run_hook() {
  # run_hook <json>
  # Use a here-document to avoid shell quoting issues with JSON containing special characters
  run bash -c "cat <<'JSON_END' | python3 '$HOOK' 2>/dev/null
$1
JSON_END"
}

@test "silent on an unrelated Bash command" {
  run_hook '{"tool_input": {"command": "ls -la"}}'

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "silent on a read-only task command" {
  run_hook '{"tool_input": {"command": "task 518 info"}}'

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "nudges on task done by bare integer ID" {
  run_hook '{"tool_input": {"command": "task 518 done"}}'

  [ "$status" -eq 0 ]
  [[ "$output" == *'"permissionDecision": "allow"'* ]]
  [[ "$output" == *"518"* ]]
}

@test "nudges on task annotate/modify/depends/delete/start/stop by bare ID" {
  for verb in annotate modify depends delete start stop; do
    run_hook "{\"tool_input\": {\"command\": \"task 42 $verb\"}}"
    [ "$status" -eq 0 ]
    [[ "$output" == *"additionalContext"* ]]
  done
}

@test "silent on a git commit with no task reference" {
  run_hook '{"tool_input": {"command": "git commit -m \"fix: typo\""}}'

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "nudges on a git commit -m citing a bare integer ID" {
  run_hook '{"tool_input": {"command": "git commit -m \"fix: matches taskwarrior 518\""}}'

  [ "$status" -eq 0 ]
  [[ "$output" == *"additionalContext"* ]]
  [[ "$output" == *"518"* ]]
}

@test "nudges on a git commit heredoc body citing a bare integer ID (the real incident's shape)" {
  run_hook '{"tool_input": {"command": "git commit -m \"$(cat <<'"'"'EOF'"'"'\nmatching picklehome'"'"'s already-deployed fix (taskwarrior 518).\nEOF\n)\""}}'

  [ "$status" -eq 0 ]
  [[ "$output" == *"additionalContext"* ]]
}

@test "silent on a git commit citing a UUID, not an integer" {
  run_hook '{"tool_input": {"command": "git commit -m \"closes taskwarrior c9dca83f\""}}'

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "fails silently on malformed stdin" {
  run bash -c "echo 'not json' | python3 '$HOOK' 2>/dev/null"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}
