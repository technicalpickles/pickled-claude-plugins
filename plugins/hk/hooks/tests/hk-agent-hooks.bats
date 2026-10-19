#!/usr/bin/env bats
# Tests for the hk SessionStart and Stop hooks. hk is stubbed on PATH, so these
# cover the gating and the hand-off to `hk agent stop-hook`, not hk itself.

START="$BATS_TEST_DIRNAME/../session-start-hk-instructions.sh"
STOP="$BATS_TEST_DIRNAME/../stop-hk-check.sh"

setup() {
  PROJECT="$BATS_TEST_TMPDIR/project"
  STUB_BIN="$BATS_TEST_TMPDIR/bin"
  CALLS="$BATS_TEST_TMPDIR/calls"
  mkdir -p "$PROJECT/sub/dir" "$STUB_BIN"
  touch "$PROJECT/hk.pkl"

  cat > "$STUB_BIN/hk" <<'STUB'
#!/usr/bin/env bash
case "$1" in
  --version)
    [ -z "${HK_STUB_BROKEN:-}" ] && echo "hk 2.7.1" || { echo "mise: no version set" >&2; exit 1; } ;;
  agent)
    case "$2" in
      stop-hook)
        if [ "${3:-}" = "--help" ]; then
          # hk before 2.5: clap usage error, exit 2
          [ -n "${HK_STUB_OLD:-}" ] && { echo "error: unrecognized subcommand 'stop-hook'" >&2; exit 2; }
          exit 0
        fi
        echo "args: $*" > "$HK_STUB_CALLS"
        echo "stdin: $(cat)" >> "$HK_STUB_CALLS"
        echo "pwd: $PWD" >> "$HK_STUB_CALLS"
        echo "${HK_STUB_STOP_OUT:-}" ;;
      instructions) echo "- stub hk instructions" ;;
    esac ;;
esac
STUB
  chmod +x "$STUB_BIN/hk"
  export PATH="$STUB_BIN:$PATH"
  export HK_STUB_CALLS="$CALLS"
}

payload() { # payload <cwd>
  jq -nc --arg cwd "$1" '{cwd: $cwd, stop_hook_active: false}'
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

@test "SessionStart accepts the other config locations hk reads" {
  for cfg in hk.local.pkl .config/hk.pkl .config/hk.local.pkl; do
    rm -f "$PROJECT/hk.pkl" "$PROJECT/hk.local.pkl"; rm -rf "$PROJECT/.config"
    mkdir -p "$(dirname "$PROJECT/$cfg")"; touch "$PROJECT/$cfg"

    run bash "$START" <<< "$(payload "$PROJECT")"

    [ "$status" -eq 0 ]
    [[ "$output" == *"stub hk instructions"* ]]
  done
}

@test "SessionStart is silent without an hk config" {
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

@test "SessionStart is silent on hk older than 2.5" {
  HK_STUB_OLD=1 run bash "$START" <<< "$(payload "$PROJECT")"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "SessionStart is silent when hk is not installed" {
  rm "$STUB_BIN/hk"

  PATH="$STUB_BIN:/usr/bin:/bin" run bash "$START" <<< "$(payload "$PROJECT")"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "Stop hands off to hk agent stop-hook with hk's own flags" {
  run bash "$STOP" <<< "$(payload "$PROJECT")"

  [ "$status" -eq 0 ]
  grep -q -- 'args: agent stop-hook --target claude-code --timeout 570' "$CALLS"
}

@test "Stop passes the hook payload through on stdin" {
  run bash "$STOP" <<< "$(payload "$PROJECT")"

  grep -q '^stdin: .*"stop_hook_active": *false' "$CALLS"
}

@test "Stop runs hk from the project directory" {
  run bash "$STOP" <<< "$(payload "$PROJECT/sub/dir")"

  grep -q "pwd: .*project/sub/dir" "$CALLS"
}

@test "Stop relays hk's block decision and exit status unchanged" {
  HK_STUB_STOP_OUT='{"decision":"block","reason":"hk check exited with status 1."}' run bash "$STOP" <<< "$(payload "$PROJECT")"

  [ "$status" -eq 0 ]
  echo "$output" | jq -e '.decision == "block"'
}

@test "Stop is silent without an hk config" {
  rm "$PROJECT/hk.pkl"

  run bash "$STOP" <<< "$(payload "$PROJECT")"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
  [ ! -e "$CALLS" ]
}

@test "Stop is silent on hk older than 2.5, where agent stop-hook is a usage error" {
  HK_STUB_OLD=1 run bash "$STOP" <<< "$(payload "$PROJECT")"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "Stop is silent when hk does not run" {
  HK_STUB_BROKEN=1 run bash "$STOP" <<< "$(payload "$PROJECT")"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
  [ ! -e "$CALLS" ]
}
