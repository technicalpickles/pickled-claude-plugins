#!/usr/bin/env bats

PLUGIN_DIR="$BATS_TEST_DIRNAME/.."
SCRIPT="$PLUGIN_DIR/skills/park/scripts/get-session-id.sh"

@test "get-session-id.sh prints CLAUDE_CODE_SESSION_ID" {
  run env -i CLAUDE_CODE_SESSION_ID=abc-123 sh "$SCRIPT"
  [ "$status" -eq 0 ]
  [ "$output" = "abc-123" ]
}

@test "get-session-id.sh falls back to CLAUDE_SESSION_ID" {
  run env -i CLAUDE_SESSION_ID=def-456 sh "$SCRIPT"
  [ "$status" -eq 0 ]
  [ "$output" = "def-456" ]
}

@test "get-session-id.sh prints nothing when no session var is set" {
  run env -i sh "$SCRIPT"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# Claude Code fills in the skill body before its first API call, so pointing the
# API at a closed port still leaves the expanded body in the transcript.
@test "/agent-meta:park body carries the session ID without inference" {
  command -v claude >/dev/null || skip "claude CLI not installed"
  work="$BATS_TEST_TMPDIR/work"
  config="$BATS_TEST_TMPDIR/config"
  mkdir -p "$work" "$config"
  sid=$(uuidgen | tr 'A-Z' 'a-z')

  cd "$work"
  run env -u CLAUDE_CODE_OAUTH_TOKEN \
    CLAUDE_CONFIG_DIR="$config" \
    ANTHROPIC_API_KEY=sk-ant-dummy \
    ANTHROPIC_BASE_URL=http://127.0.0.1:9 \
    CLAUDE_CODE_MAX_RETRIES=0 \
    CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 \
    claude -p --plugin-dir "$PLUGIN_DIR" --session-id "$sid" "/agent-meta:park continuation"

  transcript=$(find "$config/projects" -name "$sid.jsonl" | head -1)
  [ -n "$transcript" ] || { echo "no transcript for $sid"; false; }
  grep -q 'Before Writing' "$transcript" || { echo "park body was not expanded"; false; }
  grep -qF "**Session ID:** \`$sid\`" "$transcript" || { echo "expanded park body lacks $sid"; false; }
}
