#!/usr/bin/env bats
# Tests for the hk PostToolUse and Stop hooks. hk is stubbed on PATH, so these
# cover the gating and the hand-off to `hk agent stop-hook`, not hk itself.

START="$BATS_TEST_DIRNAME/../post-tool-hk-instructions.sh"
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
    [ -z "${HK_STUB_BROKEN:-}" ] && echo "hk ${HK_STUB_VERSION:-2.7.1}" || { echo "mise: no version set" >&2; exit 1; } ;;
  agent)
    case "$2" in
      stop-hook)
        echo "args: $*" > "$HK_STUB_CALLS"
        echo "stdin: $(cat)" >> "$HK_STUB_CALLS"
        echo "pwd: $PWD" >> "$HK_STUB_CALLS"
        echo "${HK_STUB_STOP_OUT:-}" ;;
      instructions)
        echo "instructions pwd: $PWD" >> "$HK_STUB_CALLS"
        echo "- stub hk instructions" ;;
    esac ;;
esac
STUB
  chmod +x "$STUB_BIN/hk"
  export PATH="$STUB_BIN:$PATH"
  export HK_STUB_CALLS="$CALLS"
  export TMPDIR="$BATS_TEST_TMPDIR/tmp"
  mkdir -p "$TMPDIR"
}

payload() { # payload <cwd> [session_id]
  jq -nc --arg cwd "$1" --arg sid "${2:-sess-1}" \
    '{session_id: $sid, cwd: $cwd, tool_name: "Bash", stop_hook_active: false}'
}

@test "PostToolUse injects hk instructions as additionalContext" {
  run bash "$START" <<< "$(payload "$PROJECT")"

  [ "$status" -eq 0 ]
  echo "$output" | jq -e '.hookSpecificOutput.hookEventName == "PostToolUse"'
  [[ "$(echo "$output" | jq -r '.hookSpecificOutput.additionalContext')" == *"stub hk instructions"* ]]
}

@test "PostToolUse finds hk.pkl above the working directory" {
  run bash "$START" <<< "$(payload "$PROJECT/sub/dir")"

  [ "$status" -eq 0 ]
  [[ "$output" == *"stub hk instructions"* ]]
}

@test "PostToolUse accepts the other config locations hk reads" {
  for cfg in hk.local.pkl .config/hk.pkl .config/hk.local.pkl; do
    rm -f "$PROJECT/hk.pkl" "$PROJECT/hk.local.pkl"; rm -rf "$PROJECT/.config"
    mkdir -p "$(dirname "$PROJECT/$cfg")"; touch "$PROJECT/$cfg"

    run bash "$START" <<< "$(payload "$PROJECT" "cfg-$cfg")"

    [ "$status" -eq 0 ]
    [[ "$output" == *"stub hk instructions"* ]]
  done
}

@test "PostToolUse is silent without an hk config" {
  rm "$PROJECT/hk.pkl"

  run bash "$START" <<< "$(payload "$PROJECT")"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "PostToolUse is silent when hk does not run (mise shim, no version set)" {
  HK_STUB_BROKEN=1 run bash "$START" <<< "$(payload "$PROJECT")"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "PostToolUse is silent on hk 2.5" {
  HK_STUB_VERSION=2.5.4 run bash "$START" <<< "$(payload "$PROJECT")"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "PostToolUse is silent when hk is not installed" {
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

@test "Stop runs hk from the working directory the hook payload names" {
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

@test "Stop is silent on hk 2.5, which blocks when there is no check hook" {
  HK_STUB_VERSION=2.5.4 run bash "$STOP" <<< "$(payload "$PROJECT")"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "Stop is silent when hk does not run" {
  HK_STUB_BROKEN=1 run bash "$STOP" <<< "$(payload "$PROJECT")"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
  [ ! -e "$CALLS" ]
}

@test "PostToolUse injects once per session, not on every tool call" {
  run bash "$START" <<< "$(payload "$PROJECT" sess-1)"
  [[ "$output" == *"stub hk instructions"* ]]

  run bash "$START" <<< "$(payload "$PROJECT" sess-1)"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "PostToolUse injects again for a different session" {
  run bash "$START" <<< "$(payload "$PROJECT" sess-1)"
  run bash "$START" <<< "$(payload "$PROJECT" sess-2)"

  [[ "$output" == *"stub hk instructions"* ]]
}

@test "PostToolUse waits for the first call inside an hk project, outside ones cost nothing" {
  OUTSIDE="$BATS_TEST_TMPDIR/outside"
  mkdir -p "$OUTSIDE"

  run bash "$START" <<< "$(payload "$OUTSIDE" sess-1)"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
  [ ! -e "$CALLS" ]

  run bash "$START" <<< "$(payload "$PROJECT" sess-1)"
  [[ "$output" == *"stub hk instructions"* ]]
}

@test "PostToolUse runs hk from the directory the tool call ended in" {
  run bash "$START" <<< "$(payload "$PROJECT/sub/dir")"

  grep -q "instructions pwd: .*project/sub/dir" "$CALLS"
}

@test "PostToolUse stays silent when the payload has no session_id" {
  run bash "$START" <<< "$(jq -nc --arg cwd "$PROJECT" '{cwd: $cwd}')"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "version gate: 2.6.0 and later are ready, earlier or unparseable are not" {
  for v in 2.6.0 2.7.1 2.10.0 3.0.0; do
    HK_STUB_VERSION=$v run bash "$START" <<< "$(payload "$PROJECT" "v-$v")"
    [[ "$output" == *"stub hk instructions"* ]] || { echo "expected ready on $v"; return 1; }
  done
  for v in 2.5.9 2.0.0 1.55.0 1.40.0 garbage; do
    HK_STUB_VERSION=$v run bash "$START" <<< "$(payload "$PROJECT" "v-$v")"
    [ -z "$output" ] || { echo "expected silent on $v"; return 1; }
  done
}
