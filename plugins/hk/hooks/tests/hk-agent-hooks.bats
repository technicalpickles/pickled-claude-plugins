#!/usr/bin/env bats
# Tests for the hk SessionStart and Stop hooks. hk is stubbed on PATH, so these
# cover the gating and exit-code mapping, not hk itself.

START="$BATS_TEST_DIRNAME/../session-start-hk-instructions.sh"
STOP="$BATS_TEST_DIRNAME/../stop-hk-check.sh"

setup() {
  PROJECT="$BATS_TEST_TMPDIR/project"
  STUB_BIN="$BATS_TEST_TMPDIR/bin"
  mkdir -p "$PROJECT/sub/dir" "$STUB_BIN"
  touch "$PROJECT/hk.pkl"

  cat > "$STUB_BIN/hk" <<'STUB'
#!/usr/bin/env bash
case "$1" in
  --version) [ -z "${HK_STUB_BROKEN:-}" ] && echo "hk 2.0.0" || { echo "mise: no version set" >&2; exit 1; } ;;
  agent) echo "- stub hk instructions" ;;
  run) echo "${HK_STUB_CHECK_OUT:-}"; exit "${HK_STUB_CHECK_EXIT:-0}" ;;
esac
STUB
  chmod +x "$STUB_BIN/hk"
  export PATH="$STUB_BIN:$PATH"
}

payload() { # payload <cwd> [stop_hook_active]
  jq -n --arg cwd "$1" --argjson active "${2:-false}" '{cwd: $cwd, stop_hook_active: $active}'
}

@test "SessionStart injects hk instructions as additionalContext" {
  run bash "$START" <<< "$(payload "$PROJECT")"

  [ "$status" -eq 0 ]
  echo "$output" | jq -e '.hookSpecificOutput.hookEventName == "SessionStart"'
  [[ "$(echo "$output" | jq -r '.hookSpecificOutput.additionalContext')" == *"stub hk instructions"* ]]
}

@test "SessionStart finds hk.pkl above the working directory" {
  run bash "$START" <<< "$(payload "$PROJECT/sub/dir")"

  [ "$status" -eq 0 ]
  [[ "$output" == *"stub hk instructions"* ]]
}

@test "SessionStart is silent without an hk.pkl" {
  rm "$PROJECT/hk.pkl"

  run bash "$START" <<< "$(payload "$PROJECT")"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "SessionStart is silent when hk does not run (mise shim, no version set)" {
  HK_STUB_BROKEN=1 run bash "$START" <<< "$(payload "$PROJECT")"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "SessionStart is silent when hk is not installed" {
  rm "$STUB_BIN/hk"

  PATH="$STUB_BIN:/usr/bin:/bin" run bash "$START" <<< "$(payload "$PROJECT")"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "Stop passes when the check passes" {
  run bash "$STOP" <<< "$(payload "$PROJECT")"

  [ "$status" -eq 0 ]
}

@test "Stop blocks with exit 2 and surfaces hk's output when the check fails" {
  HK_STUB_CHECK_EXIT=1 HK_STUB_CHECK_OUT='{"summary":"1 failed"}' run bash "$STOP" <<< "$(payload "$PROJECT")"

  [ "$status" -eq 2 ]
  [[ "$output" == *'"summary":"1 failed"'* ]]
}

@test "Stop does not block when hk.pkl has no check hook" {
  HK_STUB_CHECK_EXIT=1 HK_STUB_CHECK_OUT="Error: Hook 'check' not found" run bash "$STOP" <<< "$(payload "$PROJECT")"

  [ "$status" -eq 0 ]
}

@test "Stop does not loop when stop_hook_active is set" {
  HK_STUB_CHECK_EXIT=1 run bash "$STOP" <<< "$(payload "$PROJECT" true)"

  [ "$status" -eq 0 ]
}

@test "Stop is silent without an hk.pkl even if the check would fail" {
  rm "$PROJECT/hk.pkl"

  HK_STUB_CHECK_EXIT=1 run bash "$STOP" <<< "$(payload "$PROJECT")"

  [ "$status" -eq 0 ]
}

@test "Stop is silent when hk does not run" {
  HK_STUB_BROKEN=1 HK_STUB_CHECK_EXIT=1 run bash "$STOP" <<< "$(payload "$PROJECT")"

  [ "$status" -eq 0 ]
}
