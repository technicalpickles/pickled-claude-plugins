#!/usr/bin/env bats
# Tests for the PreToolUse:Write|Edit hook that nudges on a bare taskwarrior
# integer-ID citation in the content being written. Deliberately not scoped
# to any file path -- see the plan header for why.

HOOK="$BATS_TEST_DIRNAME/../nudge-durable-write-bare-id.py"

run_hook() {
  # run_hook <json>
  run bash -c "echo '$1' | python3 '$HOOK' 2>/dev/null"
}

@test "silent when content has no task reference at all" {
  run_hook '{"tool_input": {"file_path": "CLAUDE.md", "content": "Nothing to see here."}}'

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "silent when the citation is already a UUID" {
  run_hook '{"tool_input": {"file_path": "CLAUDE.md", "content": "see taskwarrior c9dca83f for context"}}'

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "nudges on a bare integer ID in CLAUDE.md (the file the real incident hit)" {
  run_hook '{"tool_input": {"file_path": "CLAUDE.md", "content": "replaced 2026-09-13, see taskwarrior 518"}}'

  [ "$status" -eq 0 ]
  [[ "$output" == *'"permissionDecision": "allow"'* ]]
  [[ "$output" == *"additionalContext"* ]]
  [[ "$output" == *"518"* ]]
}

@test "nudges on a bare integer ID in a non-durable-looking path (no path filtering)" {
  run_hook '{"tool_input": {"file_path": "docs/setup-notes.md", "content": "closes taskwarrior 71701d18 and see task 518 for the follow-up"}}'

  [ "$status" -eq 0 ]
  [[ "$output" == *"additionalContext"* ]]
}

@test "handles Edit's new_string field the same as Write's content field" {
  run_hook '{"tool_input": {"file_path": "docs/notes.md", "new_string": "task 42 covers this"}}'

  [ "$status" -eq 0 ]
  [[ "$output" == *"additionalContext"* ]]
}

@test "fails silently on malformed stdin" {
  run bash -c "echo 'not json' | python3 '$HOOK' 2>/dev/null"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "fails silently when tool_input is missing entirely" {
  run_hook '{}'

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}
