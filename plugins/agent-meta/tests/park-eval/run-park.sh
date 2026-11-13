#!/usr/bin/env bash
# Headless park eval. Spends model tokens. Not part of CI.
#
#   run-park.sh <label> <agent-meta-plugin-dir> <reps> [runs-dir]
#
# Per rep and scenario: builds a scratch repo, hands the model the scenario
# narrative, asks it to park, and leaves the output under <runs-dir>/<label>/.
# ratelimit parks into a scratch vault (via SB_NOTE_VAULT), csvexport into
# .parkinglot/. Score with: python3 -I score.py <runs-dir>
set -u
label=$1; plugin=$2; reps=$3
HERE=$(cd "$(dirname "$0")" && pwd)
PLUGINS=$(cd "$HERE/../../.." && pwd)
RUNS=${4:-${TMPDIR:-/tmp}/park-eval-runs}
MAXJOBS=${MAXJOBS:-4}

one() { # scenario rep
  sc=$1; rep=$2
  d="$RUNS/$label/$sc-$rep"; rm -rf "$d"; mkdir -p "$d"
  "$HERE/setup.sh" "$sc" "$d/work" >/dev/null
  vault="$d/vault"; mkdir -p "$vault/Parked sessions"
  printf '# Test vault\n\n## Parking\n\nLocation: Parked sessions\n' > "$vault/CLAUDE.md"
  extra=()
  if [ "$sc" = ratelimit ]; then
    export SB_NOTE_VAULT="$vault"
    extra=(--plugin-dir "$PLUGINS/second-brain" --add-dir "$vault")
  else
    bare="$d/bare-vault"; mkdir -p "$bare"
    printf '# Test vault without a Parking section\n' > "$bare/CLAUDE.md"
    export SB_NOTE_VAULT="$bare"
    extra=(--plugin-dir "$PLUGINS/second-brain" --add-dir "$bare")
  fi
  prompt="/agent-meta:park continuation

$(cat "$HERE/scenarios/$sc.md")"
  (cd "$d/work" && timeout 420 claude -p "$prompt" \
      --plugin-dir "$plugin" "${extra[@]}" --permission-mode acceptEdits \
      --allowedTools "Skill Read Write Edit Bash(git:*) Bash(ls:*) Bash(date:*) Bash(cat:*) Bash(printf:*) Bash(pwd:*)" \
      --output-format stream-json --verbose < /dev/null > "$d/out.jsonl" 2> "$d/err.txt")
  echo "done $label/$sc-$rep"
}

for rep in $(seq 1 "$reps"); do
  for sc in ratelimit csvexport; do
    one "$sc" "$rep" &
    while [ "$(jobs -rp | wc -l)" -ge "$MAXJOBS" ]; do sleep 2; done
  done
done
wait
echo "runs: $RUNS"
