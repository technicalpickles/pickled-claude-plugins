#!/usr/bin/env bash
# Emit-only-on-change poll loop for the wait-for-it skill.
#
# Each line printed to stdout becomes one Monitor notification, so this script
# is deliberately quiet: one line on arming, one line per real change, one line
# per probe failure. Silence means "nothing changed" AND "the probe is still
# alive" — that second guarantee is why probe failure is loud.
#
# bash 3.2 compatible (macOS system bash).
# See docs/superpowers/specs/2026-08-28-wait-for-it-design.md
set -uo pipefail

probe=''
interval=60
label='watch'
once=0
max_ticks=0

while [ $# -gt 0 ]; do
  case "$1" in
    --probe)
      [ $# -ge 2 ] || { echo "watch-loop.sh: --probe requires a value" >&2; exit 2; }
      probe="$2"; shift 2 ;;
    --interval)
      [ $# -ge 2 ] || { echo "watch-loop.sh: --interval requires a value" >&2; exit 2; }
      interval="$2"; shift 2 ;;
    --label)
      [ $# -ge 2 ] || { echo "watch-loop.sh: --label requires a value" >&2; exit 2; }
      label="$2"; shift 2 ;;
    --max-ticks)
      [ $# -ge 2 ] || { echo "watch-loop.sh: --max-ticks requires a value" >&2; exit 2; }
      max_ticks="$2"; shift 2 ;;
    --once)      once=1;             shift ;;
    -h|--help)
      sed -n '2,10p' "$0"
      exit 0 ;;
    *)
      echo "watch-loop.sh: unknown argument: $1" >&2
      exit 2 ;;
  esac
done

case "$interval" in
  ''|*[!0-9.]*) echo "watch-loop.sh: --interval must be numeric" >&2; exit 2 ;;
esac
case "$max_ticks" in
  ''|*[!0-9]*) echo "watch-loop.sh: --max-ticks must be a non-negative integer" >&2; exit 2 ;;
esac

if [ -z "$probe" ]; then
  echo "watch-loop.sh: --probe is required" >&2
  exit 2
fi

# Run the probe, capture stdout+stderr, collapse to one line, preserve its
# exit code. The output is printed even on failure: a failing probe's stderr is
# the most useful thing in the whole notification.
run_probe() {
  local out rc
  out="$(eval "$probe" 2>&1)"
  rc=$?
  printf '%s' "$out" | tr '\n' ' ' | sed 's/[[:space:]][[:space:]]*/ /g; s/ *$//'
  return $rc
}

# Baseline. A probe that fails on its FIRST call means bad auth, a bad query,
# or a typo. Refuse to arm rather than sit silent for hours looking healthy.
prev="$(run_probe)"
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "$label: probe failed on arming (rc=$rc): $prev"
  exit 1
fi
echo "$label: armed, baseline=$prev"

ticks=0
while true; do
  sleep "$interval"

  cur="$(run_probe)"
  rc=$?

  ticks=$((ticks + 1))

  if [ "$rc" -ne 0 ]; then
    echo "$label: probe FAILED rc=$rc: $cur"
  elif [ "$cur" != "$prev" ]; then
    echo "$label: changed: $prev -> $cur"
    prev="$cur"
    if [ "$once" -eq 1 ]; then
      exit 0
    fi
  fi

  if [ "$max_ticks" -gt 0 ] && [ "$ticks" -ge "$max_ticks" ]; then
    exit 0
  fi
done
