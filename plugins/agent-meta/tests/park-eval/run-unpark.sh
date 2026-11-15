#!/usr/bin/env bash
# Resume check. Runs `unpark` on every ratelimit park a run-park.sh run left behind.
#
#   run-unpark.sh <label> <runs-dir>
#
# Output goes next to each park as unpark.jsonl. Score with: python3 -I score-unpark.py <runs-dir>
set -u
label=$1; RUNS=$2
HERE=$(cd "$(dirname "$0")" && pwd)
PLUGINS=$(cd "$HERE/../../.." && pwd)
MAXJOBS=${MAXJOBS:-4}

one() {
  d=$1
  park=$(find "$d/vault" -name '[0-9]*.md' | sort | tail -1)
  [ -n "$park" ] || { echo "no park in $d"; return; }
  export SB_NOTE_VAULT="$d/vault"
  (cd "$d/work" && timeout 420 claude -p "unpark $park" \
      --plugin-dir "$PLUGINS/agent-meta" --plugin-dir "$PLUGINS/second-brain" \
      --add-dir "$d/vault" --permission-mode acceptEdits \
      --allowedTools "Skill Read Write Edit Bash(git:*) Bash(make:*) Bash(python3:*) Bash(ls:*) Bash(cat:*) Bash(grep:*) Bash(date:*)" \
      --output-format stream-json --verbose < /dev/null > "$d/unpark.jsonl" 2> "$d/unpark.err")
  echo "done $d"
}

for d in "$RUNS/$label"/ratelimit-*; do
  one "$d" &
  while [ "$(jobs -rp | wc -l)" -ge "$MAXJOBS" ]; do sleep 2; done
done
wait
