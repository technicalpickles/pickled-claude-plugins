#!/usr/bin/env bats
# Payload shapes mirror what Claude Code sent a logging hook on 2026-11-14:
# a 403 as PostToolUse with code 403, a DNS failure as PostToolUseFailure.

HOOK="$BATS_TEST_DIRNAME/../webfetch-failed-ladder.py"

setup() {
  PYTHON="$(python3 -c 'import sys; print(sys.executable)')"
}

run_hook() {
  run "$PYTHON" "$HOOK" <<< "$1"
}

context() {
  printf '%s' "$output" | jq -r '.hookSpecificOutput.additionalContext'
}

@test "a 403 gets the fetch ladder" {
  run_hook '{"hook_event_name":"PostToolUse","tool_name":"WebFetch","tool_input":{"url":"https://medium.com/p/1"},"tool_response":{"bytes":0,"code":403,"codeText":"Forbidden","result":"The server returned HTTP 403 Forbidden."}}'
  [ "$status" -eq 0 ]
  [ "$(printf '%s' "$output" | jq -r '.hookSpecificOutput.hookEventName')" = "PostToolUse" ]
  [[ "$(context)" == *"https://medium.com/p/1 (HTTP 403)"* ]]
  [[ "$(context)" == *"Claude in Chrome"* ]]
}

@test "a bot-check page served as 200 gets the fetch ladder" {
  run_hook '{"hook_event_name":"PostToolUse","tool_input":{"url":"https://example.com/talk.pdf"},"tool_response":{"bytes":900,"code":200,"result":"Fetched it.\n<fetched-web-content>\nJust a moment...\nEnable JavaScript and cookies to continue\n</fetched-web-content>"}}'
  [[ "$(context)" == *"bot-check page"* ]]
}

@test "an empty body gets the fetch ladder" {
  run_hook '{"hook_event_name":"PostToolUse","tool_input":{"url":"https://example.com/"},"tool_response":{"bytes":0,"code":200,"result":""}}'
  [[ "$(context)" == *"came back empty"* ]]
}

@test "a normal page adds nothing" {
  run_hook '{"hook_event_name":"PostToolUse","tool_input":{"url":"https://httpbin.org/html"},"tool_response":{"bytes":3741,"code":200,"result":"Fetched it.\n<fetched-web-content>\nHerman Melville - Moby-Dick\n</fetched-web-content>"}}'
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "a long article that mentions captcha adds nothing" {
  body=$(head -c 6000 /dev/zero | tr '\0' 'x')
  run_hook "{\"hook_event_name\":\"PostToolUse\",\"tool_input\":{\"url\":\"https://example.com/\"},\"tool_response\":{\"bytes\":6000,\"code\":200,\"result\":\"How captcha works. $body\"}}"
  [ -z "$output" ]
}

@test "a blocked fetch reported as a failure gets the fetch ladder" {
  run_hook '{"hook_event_name":"PostToolUseFailure","tool_input":{"url":"https://example.com/"},"error":"Request failed with status code 429"}'
  [ "$(printf '%s' "$output" | jq -r '.hookSpecificOutput.hookEventName')" = "PostToolUseFailure" ]
  [[ "$(context)" == *"status code 429"* ]]
}

@test "a DNS failure adds nothing, since no browser would reach the host either" {
  run_hook '{"hook_event_name":"PostToolUseFailure","tool_input":{"url":"https://nonexistent-host-zz9.invalid/"},"error":"getaddrinfo ENOTFOUND nonexistent-host-zz9.invalid"}'
  [ -z "$output" ]
}

@test "malformed stdin fails open" {
  run_hook 'not json'
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}
