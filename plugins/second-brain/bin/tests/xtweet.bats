#!/usr/bin/env bats
# xtweet tests: a stub `xurl` on PATH returns canned API JSON, so no X
# credentials or network are needed.

XTWEET="$BATS_TEST_DIRNAME/../xtweet"

setup() {
  STUB_DIR="$(mktemp -d)"
  export PATH="$STUB_DIR:$PATH"
  cat > "$STUB_DIR/xurl" <<'STUB'
#!/usr/bin/env bash
if [[ -n "${XURL_FAIL:-}" ]]; then
  echo '{"errors":[{"code":453,"message":"boom"}]}'
else
  echo '{"data":{"id":"123","text":"hello world","created_at":"2026-01-01T00:00:00Z","author_id":"9","public_metrics":{"like_count":1,"retweet_count":2,"reply_count":3,"impression_count":4}},"includes":{"users":[{"id":"9","name":"Ann","username":"ann"}]}}'
fi
STUB
  chmod +x "$STUB_DIR/xurl"
}

teardown() {
  rm -rf "$STUB_DIR"
}

@test "--help exits 0 and prints usage" {
  run "$XTWEET" --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"usage: xtweet"* ]]
}

@test "no arguments exits 1 with usage" {
  run "$XTWEET"
  [ "$status" -eq 1 ]
  [[ "$output" == *"usage: xtweet"* ]]
}

@test "bare numeric ID formats author and text" {
  run "$XTWEET" 123
  [ "$status" -eq 0 ]
  [[ "$output" == *"Ann (@ann)"* ]]
  [[ "$output" == *"hello world"* ]]
  [[ "$output" == *"https://x.com/ann/status/123"* ]]
}

@test "status URL resolves to the same tweet as a bare ID" {
  run "$XTWEET" "https://x.com/ann/status/123"
  [ "$status" -eq 0 ]
  [[ "$output" == *"hello world"* ]]
}

@test "a string with no tweet ID exits 1 and says so" {
  run "$XTWEET" "https://example.com/not-a-tweet"
  [ "$status" -eq 1 ]
  [[ "$output" == *"couldn't find a tweet ID"* ]]
}

@test "API errors are reported, not swallowed" {
  XURL_FAIL=1 run "$XTWEET" 123
  [[ "$output" == *"API error for 123"* ]]
  [[ "$output" == *"boom"* ]]
}
