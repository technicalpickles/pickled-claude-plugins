#!/usr/bin/env bats
# Tests for diagnose-sb.sh - stubs npx/npm on PATH so no real network or
# sb install is needed.

SCRIPT="$BATS_TEST_DIRNAME/../diagnose-sb.sh"

setup() {
  FAKE_BIN="$(mktemp -d)"
  PATH="$FAKE_BIN:$PATH"
}

teardown() {
  rm -rf "$FAKE_BIN"
}

write_fake() {
  # write_fake <name> <exit-code> <stdout>
  cat > "$FAKE_BIN/$1" <<SCRIPT_EOF
#!/usr/bin/env bash
echo "$3"
exit $2
SCRIPT_EOF
  chmod +x "$FAKE_BIN/$1"
}

@test "reports sb missing when npx fails outright" {
  write_fake npx 1 "npm error could not determine executable to run"
  write_fake npm 0 "11.9.0"

  run "$SCRIPT"

  [ "$status" -eq 1 ]
  [[ "$output" == *"sb CLI is not available"* ]]
  [[ "$output" == *"npm i -g @techpickles/sb"* ]]
}

@test "detects npx misdispatching to npm itself" {
  write_fake npx 0 "11.9.0"
  write_fake npm 0 "11.9.0"

  run "$SCRIPT"

  [ "$status" -eq 1 ]
  [[ "$output" == *"misdispatching"* ]]
}

@test "reports healthy sb on the happy path" {
  write_fake npx 0 "0.4.1"
  write_fake npm 0 "11.9.0"

  run "$SCRIPT"

  [ "$status" -eq 0 ]
  [[ "$output" == *"looks fine"* ]]
  [[ "$output" == *"0.4.1"* ]]
}
