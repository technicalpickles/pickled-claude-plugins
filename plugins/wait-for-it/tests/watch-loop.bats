#!/usr/bin/env bats
# Tests for the wait-for-it skill's poll loop: baseline arming, change
# detection, loud probe failure, and bounded modes. All probes are fake and
# local — no network, no VM.
# See docs/superpowers/specs/2026-08-28-wait-for-it-design.md

setup() {
  TEST_DIR="$(cd "$(dirname "$BATS_TEST_FILENAME")" && pwd)"
  SCRIPT="$TEST_DIR/../skills/wait-for-it/watch-loop.sh"
  WORK="$(mktemp -d)"
}

teardown() {
  rm -rf "$WORK"
}

# A probe whose output changes on every call: hits=0, hits=1, hits=2, ...
make_counting_probe() {
  echo 0 > "$WORK/counter"
  cat > "$WORK/probe.sh" <<'EOS'
#!/usr/bin/env bash
n=$(cat "$1")
echo $((n + 1)) > "$1"
echo "hits=$n"
EOS
  chmod +x "$WORK/probe.sh"
  echo "$WORK/probe.sh $WORK/counter"
}

# A probe that always prints the same thing.
make_static_probe() {
  cat > "$WORK/probe.sh" <<'EOS'
#!/usr/bin/env bash
echo "hits=0"
EOS
  chmod +x "$WORK/probe.sh"
  echo "$WORK/probe.sh"
}

# A probe that succeeds once (so arming works), then fails with rc=7.
make_fails_after_first_probe() {
  cat > "$WORK/probe.sh" <<'EOS'
#!/usr/bin/env bash
if [ -f "$1" ]; then
  echo "boom"
  exit 7
fi
touch "$1"
echo "hits=0"
EOS
  chmod +x "$WORK/probe.sh"
  echo "$WORK/probe.sh $WORK/marker"
}

# A probe that succeeds once (baseline), fails once, then recovers with a
# value different from the baseline.
make_recovers_after_one_failure_probe() {
  cat > "$WORK/probe.sh" <<'EOS'
#!/usr/bin/env bash
state="$(cat "$1" 2>/dev/null || echo 0)"
case "$state" in
  0) echo 1 > "$1"; echo "hits=0" ;;
  1) echo 2 > "$1"; echo "boom"; exit 5 ;;
  *) echo "hits=1" ;;
esac
EOS
  chmod +x "$WORK/probe.sh"
  echo "$WORK/probe.sh $WORK/state"
}

@test "emits a baseline event on the first tick" {
  probe="$(make_static_probe)"
  run bash "$SCRIPT" --probe "$probe" --interval 0.05 --max-ticks 1 --label test
  [ "$status" -eq 0 ]
  [[ "${lines[0]}" == "test: armed, baseline=hits=0" ]]
}

@test "refuses to arm when the probe fails on the first call" {
  run bash "$SCRIPT" --probe 'echo nope; exit 9' --interval 0.05 --label test
  [ "$status" -eq 1 ]
  [[ "${lines[0]}" == *"probe failed on arming (rc=9)"* ]]
  [[ "$output" != *"armed, baseline"* ]]
}

@test "exits 2 with no --probe" {
  run bash "$SCRIPT" --interval 0.05
  [ "$status" -eq 2 ]
}

@test "emits exactly one changed line per change" {
  probe="$(make_counting_probe)"
  run bash "$SCRIPT" --probe "$probe" --interval 0.05 --max-ticks 2 --label test
  [ "$status" -eq 0 ]
  [[ "${lines[0]}" == "test: armed, baseline=hits=0" ]]
  [[ "${lines[1]}" == "test: changed: hits=0 -> hits=1" ]]
  [[ "${lines[2]}" == "test: changed: hits=1 -> hits=2" ]]
  [ "${#lines[@]}" -eq 3 ]
}

@test "stays silent when nothing changes" {
  probe="$(make_static_probe)"
  run bash "$SCRIPT" --probe "$probe" --interval 0.05 --max-ticks 5 --label test
  [ "$status" -eq 0 ]
  [ "${#lines[@]}" -eq 1 ]
  [[ "${lines[0]}" == "test: armed, baseline=hits=0" ]]
}

@test "collapses multi-line probe output to a single line" {
  run bash "$SCRIPT" --probe 'printf "a\nb\nc\n"' --interval 0.05 --max-ticks 1 --label test
  [ "$status" -eq 0 ]
  [[ "${lines[0]}" == "test: armed, baseline=a b c" ]]
  [ "${#lines[@]}" -eq 1 ]
}

@test "a mid-loop probe failure emits and the loop keeps going" {
  probe="$(make_fails_after_first_probe)"
  run bash "$SCRIPT" --probe "$probe" --interval 0.05 --max-ticks 3 --label test
  [ "$status" -eq 0 ]
  [[ "${lines[0]}" == "test: armed, baseline=hits=0" ]]
  [[ "${lines[1]}" == "test: probe FAILED rc=7: boom" ]]
  [[ "${lines[2]}" == "test: probe FAILED rc=7: boom" ]]
  [[ "${lines[3]}" == "test: probe FAILED rc=7: boom" ]]
  [ "${#lines[@]}" -eq 4 ]
}

@test "a failing probe never reports a spurious change" {
  probe="$(make_fails_after_first_probe)"
  run bash "$SCRIPT" --probe "$probe" --interval 0.05 --max-ticks 3 --label test
  [[ "$output" != *"changed:"* ]]
}

@test "recovering from a probe failure reports the real change, not a false one" {
  probe="$(make_recovers_after_one_failure_probe)"
  run bash "$SCRIPT" --probe "$probe" --interval 0.05 --max-ticks 2 --label test
  [ "$status" -eq 0 ]
  [[ "${lines[0]}" == "test: armed, baseline=hits=0" ]]
  [[ "${lines[1]}" == "test: probe FAILED rc=5: boom" ]]
  [[ "${lines[2]}" == "test: changed: hits=0 -> hits=1" ]]
  [ "${#lines[@]}" -eq 3 ]
}

# Deliberately no --max-ticks: if --once breaks, this hangs rather than
# failing cleanly -- that hang IS the failure signal.
@test "--once exits after the first change" {
  probe="$(make_counting_probe)"
  run bash "$SCRIPT" --probe "$probe" --interval 0.05 --once --label test
  [ "$status" -eq 0 ]
  [[ "${lines[0]}" == "test: armed, baseline=hits=0" ]]
  [[ "${lines[1]}" == "test: changed: hits=0 -> hits=1" ]]
  [ "${#lines[@]}" -eq 2 ]
}
