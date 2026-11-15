#!/usr/bin/env bats
# Tests for the skill-scoped PreToolUse:WebFetch hook - stubs lightpanda on a
# fake PATH and builds a fake session transcript, so no real lightpanda or
# Claude session is needed.

HOOK="$BATS_TEST_DIRNAME/../webfetch-prefer-lightpanda.py"

setup() {
  # The real interpreter, not a version-manager shim: shims can print their
  # own warnings to stderr, which `run` captures as hook output.
  PYTHON="$(python3 -c 'import sys; print(sys.executable)')"
  FAKE_BIN="$(mktemp -d)"
  EMPTY_BIN="$(mktemp -d)"
  printf '#!/bin/sh\nexit 0\n' > "$FAKE_BIN/lightpanda"
  chmod +x "$FAKE_BIN/lightpanda"
  TRANSCRIPT="$(mktemp)"
  ATTEMPT=0
}

teardown() {
  rm -rf "$FAKE_BIN" "$EMPTY_BIN" "$TRANSCRIPT"
}

write_attempt() {
  # write_attempt <url> <is_error: true|false> <content-json>
  ATTEMPT=$((ATTEMPT + 1))
  local id="toolu_$ATTEMPT"
  printf '{"type":"assistant","message":{"content":[{"type":"tool_use","id":"%s","name":"Bash","input":{"command":"lightpanda fetch --dump markdown %s"}}]}}\n' "$id" "$1" >> "$TRANSCRIPT"
  printf '{"type":"user","message":{"content":[{"type":"tool_result","tool_use_id":"%s","is_error":%s,"content":%s}]}}\n' "$id" "$2" "$3" >> "$TRANSCRIPT"
}

long_content() {
  # 500 chars of page text as a JSON string
  printf '"%s"' "$(head -c 500 /dev/zero | tr '\0' 'x')"
}

run_hook() {
  # run_hook <bin-dir> <url> [transcript-path]
  local transcript="${3:-$TRANSCRIPT}"
  run bash -c "printf '%s' '{\"tool_input\": {\"url\": \"$2\"}, \"transcript_path\": \"$transcript\"}' | PATH='$1:/usr/bin:/bin' '$PYTHON' '$HOOK'"
}

@test "allows silently when lightpanda is not on PATH" {
  run_hook "$EMPTY_BIN" "https://glean.com/"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "denies when lightpanda exists and was never tried" {
  run_hook "$FAKE_BIN" "https://glean.com/"
  [ "$status" -eq 0 ]
  [[ "$output" == *'"permissionDecision": "deny"'* ]]
  [[ "$output" == *"lightpanda fetch --dump markdown https://glean.com/"* ]]
}

@test "allows after failed lightpanda for the same host" {
  write_attempt "https://glean.com/" true '"Error: navigation failed"'
  run_hook "$FAKE_BIN" "https://glean.com/"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "allows after lightpanda returned near-empty output" {
  write_attempt "https://glean.com/" false '"<html></html>"'
  run_hook "$FAKE_BIN" "https://glean.com/"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "allows after failed lightpanda when result content is a block list" {
  write_attempt "https://glean.com/" true '[{"type":"text","text":"Error: navigation failed"}]'
  run_hook "$FAKE_BIN" "https://glean.com/"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "denies when the failed attempt was for a different host" {
  write_attempt "https://falconer.com/" true '"Error: navigation failed"'
  run_hook "$FAKE_BIN" "https://glean.com/"
  [ "$status" -eq 0 ]
  [[ "$output" == *'"permissionDecision": "deny"'* ]]
}

@test "denies after a successful lightpanda fetch" {
  write_attempt "https://glean.com/" false "$(long_content)"
  run_hook "$FAKE_BIN" "https://glean.com/"
  [ "$status" -eq 0 ]
  [[ "$output" == *'"permissionDecision": "deny"'* ]]
}

@test "denies with wait message while lightpanda is still running in background" {
  write_attempt "https://glean.com/" false '"Command running in background with ID: abc123"'
  run_hook "$FAKE_BIN" "https://glean.com/"
  [ "$status" -eq 0 ]
  [[ "$output" == *'"permissionDecision": "deny"'* ]]
  [[ "$output" == *"still running in the background"* ]]
}

@test "treats www and case variants as the same host" {
  write_attempt "https://glean.com/x" true '"Error: navigation failed"'
  run_hook "$FAKE_BIN" "https://www.Glean.com/y"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "most recent lightpanda attempt for the host wins" {
  write_attempt "https://glean.com/" true '"Error: navigation failed"'
  write_attempt "https://glean.com/" false "$(long_content)"
  run_hook "$FAKE_BIN" "https://glean.com/"
  [ "$status" -eq 0 ]
  [[ "$output" == *'"permissionDecision": "deny"'* ]]
}

@test "allows silently when transcript is unreadable" {
  run_hook "$FAKE_BIN" "https://glean.com/" "/nonexistent/transcript.jsonl"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "allows silently on malformed stdin" {
  run bash -c "echo 'not json' | PATH='$FAKE_BIN:/usr/bin:/bin' '$PYTHON' '$HOOK'"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}
