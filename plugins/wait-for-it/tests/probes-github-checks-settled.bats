#!/usr/bin/env bats
# Tests for the wait-for-it skill's shipped github-checks-settled probe.
# All gh calls are stubbed -- no network, no real PR.
# See docs/superpowers/specs/2026-08-28-wait-for-it-probe-scripts-design.md

setup() {
  TEST_DIR="$(cd "$(dirname "$BATS_TEST_FILENAME")" && pwd)"
  SCRIPT="$TEST_DIR/../skills/wait-for-it/probes/github-checks-settled.sh"
  WORK="$(mktemp -d)"
  mkdir -p "$WORK/bin"
  export PATH="$WORK/bin:$PATH"
}

teardown() {
  rm -rf "$WORK"
}

# A fake `gh` that records its arguments (so a test can assert the script
# forwarded the right repo/PR number) and always prints the given JSON,
# exit 0. Overwriting $WORK/bin/gh between calls in the same test lets a
# test simulate the check set changing across two calls.
make_fake_gh() {
  cat > "$WORK/bin/gh" <<EOS
#!/usr/bin/env bash
echo "\$@" > "$WORK/gh-args"
echo '$1'
EOS
  chmod +x "$WORK/bin/gh"
}

# A fake `gh` that fails, the way an expired-auth or bad-repo call would.
make_fake_gh_failing() {
  cat > "$WORK/bin/gh" <<'EOS'
#!/usr/bin/env bash
echo "error: authentication required" >&2
exit 4
EOS
  chmod +x "$WORK/bin/gh"
}

@test "prints empty pending when all checks are settled" {
  make_fake_gh '[{"name":"a","bucket":"pass"},{"name":"b","bucket":"pass"}]'
  run "$SCRIPT" myorg/myrepo 42
  [ "$status" -eq 0 ]
  [ "$output" = "pending:" ]
}

@test "names the checks still pending, sorted" {
  make_fake_gh '[{"name":"z-check","bucket":"pending"},{"name":"a-check","bucket":"pending"},{"name":"done","bucket":"pass"}]'
  run "$SCRIPT" myorg/myrepo 42
  [ "$status" -eq 0 ]
  [ "$output" = "pending:a-check,z-check" ]
}

@test "regression: a growing total check count between calls does not corrupt pending output" {
  # First call: 2 checks, 1 pending.
  make_fake_gh '[{"name":"a","bucket":"pass"},{"name":"b","bucket":"pending"}]'
  run "$SCRIPT" myorg/myrepo 42
  [ "$status" -eq 0 ]
  [ "$output" = "pending:b" ]

  # Second call: a rerun added a third check; a different one is now pending.
  # This is the exact shape of the bug found live on a real PR --
  # the total grew from 11 to 15 mid-watch. The old "count of non-pending
  # checks" recipe would have misjudged this; pending-names never needs the
  # total.
  make_fake_gh '[{"name":"a","bucket":"pass"},{"name":"b","bucket":"pass"},{"name":"c","bucket":"pending"}]'
  run "$SCRIPT" myorg/myrepo 42
  [ "$status" -eq 0 ]
  [ "$output" = "pending:c" ]
}

@test "propagates a gh failure instead of printing a false pending line" {
  make_fake_gh_failing
  run "$SCRIPT" myorg/myrepo 42
  # Exact rc, not just nonzero -- the plan's locked interface says the script
  # "exits with gh's own exit code" on failure. An implementation that
  # swallows gh's real rc and always exits e.g. 1 would pass a looser check.
  [ "$status" -eq 4 ]
  # Bare `[[ ]]` that isn't the test's last statement doesn't actually gate
  # pass/fail here -- bash's errexit doesn't fire on a failing bare `[[ ]]`
  # mid-test (confirmed empirically), only on the function's last command.
  # Combine both conditions into one `[[ ]]` so the check that matters is
  # the last statement.
  [[ "$output" == *"authentication required"* && "$output" != "pending:"* ]]
}

@test "exits 2 with the wrong argument count" {
  run "$SCRIPT" only-one-arg
  [ "$status" -eq 2 ]
}

@test "forwards the repo and pr number to gh pr checks" {
  make_fake_gh '[{"name":"a","bucket":"pass"}]'
  run "$SCRIPT" myorg/myrepo 42
  [ "$status" -eq 0 ]
  recorded="$(cat "$WORK/gh-args")"
  [[ "$recorded" == *"pr checks 42"* && "$recorded" == *"--repo myorg/myrepo"* && "$recorded" == *"--json name,bucket"* ]]
}
