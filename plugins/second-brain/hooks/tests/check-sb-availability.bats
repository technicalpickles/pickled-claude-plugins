#!/usr/bin/env bats
# Tests for the PostToolUse:Skill hook - stubs npx on PATH via a fake
# CLAUDE_PLUGIN_ROOT/scripts/diagnose-sb.sh so no real sb install is needed.

HOOK="$BATS_TEST_DIRNAME/../check-sb-availability.py"

setup() {
  FAKE_ROOT="$(mktemp -d)"
  mkdir -p "$FAKE_ROOT/scripts"
}

teardown() {
  rm -rf "$FAKE_ROOT"
}

write_fake_diagnose() {
  # write_fake_diagnose <exit-code> <stdout>
  cat > "$FAKE_ROOT/scripts/diagnose-sb.sh" <<SCRIPT_EOF
#!/usr/bin/env bash
echo "$2"
exit $1
SCRIPT_EOF
  chmod +x "$FAKE_ROOT/scripts/diagnose-sb.sh"
}

@test "ignores skills outside the sb-dependent set" {
  write_fake_diagnose 1 "should never run"

  run bash -c "echo '{\"tool_input\": {\"skill\": \"second-brain:connect\"}}' | CLAUDE_PLUGIN_ROOT='$FAKE_ROOT' python3 '$HOOK'"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "stays silent when sb is healthy" {
  write_fake_diagnose 0 "sb CLI looks fine (version: 0.4.1)."

  run bash -c "echo '{\"tool_input\": {\"skill\": \"second-brain:setup\"}}' | CLAUDE_PLUGIN_ROOT='$FAKE_ROOT' python3 '$HOOK'"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "injects additionalContext when sb is broken" {
  write_fake_diagnose 1 "sb CLI is not available (npx exited 1)."

  run bash -c "echo '{\"tool_input\": {\"skill\": \"second-brain:route\"}}' | CLAUDE_PLUGIN_ROOT='$FAKE_ROOT' python3 '$HOOK'"

  [ "$status" -eq 0 ]
  [[ "$output" == *"additionalContext"* ]]
  [[ "$output" == *"sb CLI is not available"* ]]
}

@test "fails silently on malformed stdin" {
  run bash -c "echo 'not json' | CLAUDE_PLUGIN_ROOT='$FAKE_ROOT' python3 '$HOOK'"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}
