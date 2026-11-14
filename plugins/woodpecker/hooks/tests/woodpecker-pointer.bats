#!/usr/bin/env bats

HOOK="$BATS_TEST_DIRNAME/../woodpecker-pointer.sh"

setup() {
  WP_REPO="$BATS_TEST_TMPDIR/wp-repo"
  OTHER="$BATS_TEST_TMPDIR/other"
  mkdir -p "$WP_REPO/sub/dir" "$OTHER"
  touch "$WP_REPO/.woodpecker.yml"
  export TMPDIR="$BATS_TEST_TMPDIR/tmp"
  mkdir -p "$TMPDIR"
}

session_start() { # session_start <cwd>
  jq -nc --arg cwd "$1" '{hook_event_name: "SessionStart", cwd: $cwd, session_id: "s1"}'
}

bash_call() { # bash_call <cwd> <session> <command> <stdout>
  jq -nc --arg cwd "$1" --arg s "$2" --arg c "$3" --arg o "$4" '{
    hook_event_name: "PostToolUse", cwd: $cwd, session_id: $s, tool_name: "Bash",
    tool_input: {command: $c}, tool_response: {stdout: $o, stderr: ""}
  }'
}

context() {
  echo "$output" | jq -r '.hookSpecificOutput.additionalContext'
}

@test "SessionStart points at both skills in a repo with .woodpecker.yml" {
  run bash "$HOOK" <<< "$(session_start "$WP_REPO")"

  [ "$status" -eq 0 ]
  echo "$output" | jq -e '.hookSpecificOutput.hookEventName == "SessionStart"'
  [[ "$(context)" == *"woodpecker:woodpecker-investigating-pipelines"* ]]
  [[ "$(context)" == *"woodpecker:woodpecker-authoring-pipelines"* ]]
}

@test "SessionStart finds the config above the working directory" {
  run bash "$HOOK" <<< "$(session_start "$WP_REPO/sub/dir")"

  [ "$status" -eq 0 ]
  [[ "$(context)" == *"builds with Woodpecker CI"* ]]
}

@test "SessionStart accepts .woodpecker.yaml and a .woodpecker/ directory" {
  rm "$WP_REPO/.woodpecker.yml"
  touch "$WP_REPO/.woodpecker.yaml"
  run bash "$HOOK" <<< "$(session_start "$WP_REPO")"
  [[ "$(context)" == *"builds with Woodpecker CI"* ]]

  rm "$WP_REPO/.woodpecker.yaml"
  mkdir "$WP_REPO/.woodpecker"
  run bash "$HOOK" <<< "$(session_start "$WP_REPO")"
  [[ "$(context)" == *"builds with Woodpecker CI"* ]]
}

@test "SessionStart is silent without a Woodpecker config" {
  run bash "$HOOK" <<< "$(session_start "$OTHER")"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "PostToolUse points once when output shows a Woodpecker status outside a Woodpecker repo" {
  checks=$'check\tpass\t1m\thttps://ci.example.com/repos/2/pipeline/95\nci/woodpecker/push/woodpecker\tpass'

  run bash "$HOOK" <<< "$(bash_call "$OTHER" s1 "gh pr checks 68 --repo o/r" "$checks")"
  [ "$status" -eq 0 ]
  echo "$output" | jq -e '.hookSpecificOutput.hookEventName == "PostToolUse"'
  [[ "$(context)" == *"woodpecker:woodpecker-investigating-pipelines"* ]]

  run bash "$HOOK" <<< "$(bash_call "$OTHER" s1 "gh pr checks 68 --repo o/r" "$checks")"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "PostToolUse matches each Woodpecker signal" {
  n=0
  for cmd in "cat .woodpecker.yml" "ls .woodpecker/" "woodpecker-cli lint ." "open https://ci.example.com/repos/3/pipeline/42"; do
    n=$((n + 1))
    run bash "$HOOK" <<< "$(bash_call "$OTHER" "sig$n" "$cmd" "")"
    [[ "$(context)" == *"touched Woodpecker CI"* ]]
  done
}

@test "PostToolUse matches a Read of a pipeline file" {
  payload=$(jq -nc --arg cwd "$OTHER" '{
    hook_event_name: "PostToolUse", cwd: $cwd, session_id: "r1", tool_name: "Read",
    tool_input: {file_path: "/src/app/.woodpecker/test.yaml"}, tool_response: {}
  }')

  run bash "$HOOK" <<< "$payload"
  [[ "$(context)" == *"touched Woodpecker CI"* ]]
}

@test "PostToolUse ignores tool calls with no Woodpecker signal" {
  run bash "$HOOK" <<< "$(bash_call "$OTHER" s2 "gh pr checks 3" "build pass buildkite/pipeline")"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "PostToolUse stays silent in a Woodpecker repo, where SessionStart already pointed" {
  run bash "$HOOK" <<< "$(bash_call "$WP_REPO" s3 "cat .woodpecker.yml" "")"

  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "PostToolUse without a session id stays silent" {
  payload=$(bash_call "$OTHER" "" "cat .woodpecker.yml" "" | jq -c 'del(.session_id)')

  run bash "$HOOK" <<< "$payload"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}
