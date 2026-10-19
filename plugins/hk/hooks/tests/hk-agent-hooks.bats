#!/usr/bin/env bats
# Tests for the hk SessionStart and Stop hooks. hk is stubbed on PATH, so these
# cover the gating and the hand-off to `hk agent stop-hook`, not hk itself.

START="$BATS_TEST_DIRNAME/../session-start-hk-instructions.sh"
STOP="$BATS_TEST_DIRNAME/../stop-hk-check.sh"
MCP="$BATS_TEST_DIRNAME/../hk-mcp.sh"

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
  mcp)
    echo "args: $*" > "$HK_STUB_CALLS"
    echo "stub hk mcp" ;;
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

mcp_request() { # mcp_request <id> <method>
  jq -nc --argjson id "$1" --arg method "$2" \
    '{jsonrpc: "2.0", id: $id, method: $method, params: {protocolVersion: "2025-06-18"}}'
}

@test "MCP launcher becomes hk mcp for the project root in an hk project" {
  run bash "$MCP" "$PROJECT" <<< "$(mcp_request 1 initialize)"

  [ "$status" -eq 0 ]
  [[ "$output" == *"stub hk mcp"* ]]
  grep -q -- "args: mcp --root $PROJECT" "$CALLS"
}

@test "MCP launcher serves an inert session when the project has no hk config" {
  rm "$PROJECT/hk.pkl"

  run bash "$MCP" "$PROJECT" <<< "$(mcp_request 1 initialize)"

  [ "$status" -eq 0 ]
  echo "$output" | jq -e '.id == 1 and .result.serverInfo.version == "inactive" and .result.capabilities == {}'
  [ ! -e "$CALLS" ]
}

@test "MCP launcher serves an inert session on hk older than 2.5" {
  HK_STUB_OLD=1 run bash "$MCP" "$PROJECT" <<< "$(mcp_request 1 initialize)"

  [ "$status" -eq 0 ]
  echo "$output" | jq -e '.result.serverInfo.version == "inactive"'
  [ ! -e "$CALLS" ]
}

@test "MCP inert session echoes the client's protocol version, answers ping, ignores notifications" {
  rm "$PROJECT/hk.pkl"
  requests=$(printf '%s\n' \
    "$(jq -nc '{jsonrpc: "2.0", id: 7, method: "initialize", params: {protocolVersion: "2024-11-05"}}')" \
    '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
    "$(mcp_request 8 ping)" \
    "$(mcp_request 9 tools/list)")

  run bash "$MCP" "$PROJECT" <<< "$requests"

  [ "$status" -eq 0 ]
  [ "$(echo "$output" | wc -l | tr -d ' ')" -eq 3 ]
  echo "$output" | sed -n 1p | jq -e '.result.protocolVersion == "2024-11-05"'
  echo "$output" | sed -n 2p | jq -e '.id == 8 and .result == {}'
  echo "$output" | sed -n 3p | jq -e '.id == 9 and .error.code == -32601'
}

@test "MCP launcher falls back when the project dir argument is not a directory" {
  export CLAUDE_PROJECT_DIR="$PROJECT"

  run bash "$MCP" '${CLAUDE_PROJECT_DIR}' <<< "$(mcp_request 1 initialize)"

  [ "$status" -eq 0 ]
  grep -q -- "args: mcp --root $PROJECT" "$CALLS"
}
