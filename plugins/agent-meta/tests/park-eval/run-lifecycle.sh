#!/usr/bin/env bash
# Headless lifecycle eval (re-park supersedes, wrapped-file gate, stale sweep). Spends tokens.
#
#   run-lifecycle.sh <label> <agent-meta-plugin-dir> <reps> [runs-dir]
#
# Each cell is one or two `claude -p` calls in a scratch repo and scratch vault. Two-call cells
# resume the first call's session (--resume), so the second call sees the first in its transcript.
# Score with: python3 -I score-lifecycle.py <runs-dir>
set -u
label=$1; plugin=$2; reps=$3
HERE=$(cd "$(dirname "$0")" && pwd)
PLUGINS=$(cd "$HERE/../../.." && pwd)
RUNS=${4:-${TMPDIR:-/tmp}/park-eval-runs}
MAXJOBS=${MAXJOBS:-4}
TOOLS="Skill Read Write Edit AskUserQuestion Bash(git:*) Bash(ls:*) Bash(date:*) Bash(cat:*) Bash(printf:*) Bash(pwd:*) Bash(rm:*) Bash(task:*) Bash(make:*) Bash(grep:*) Bash(python3:*)"

call() { # dir prompt outfile [resume-session]
  local d=$1 prompt=$2 out=$3 sid=${4:-}
  local sess=(); [ -n "$sid" ] && sess=(--resume "$sid")
  (cd "$d/work" && timeout 420 claude -p "$prompt" "${sess[@]}" \
      --plugin-dir "$plugin" --plugin-dir "$PLUGINS/second-brain" --add-dir "$d/vault" \
      --permission-mode acceptEdits --allowedTools "$TOOLS" \
      --output-format stream-json --verbose < /dev/null > "$d/$out" 2> "$d/$out.err")
}
sid_of() { python3 -I -c "
import json,sys
for l in open(sys.argv[1]):
    try: e=json.loads(l)
    except ValueError: continue
    if e.get('session_id'): print(e['session_id']); break" "$1"; }

one() { # cell rep
  cell=$1; rep=$2
  d="$RUNS/$label/$cell-$rep"; rm -rf "$d"; mkdir -p "$d"
  "$HERE/lifecycle-setup.sh" "$cell" "$d" >/dev/null
  export SB_NOTE_VAULT="$d/vault"
  if [ "$cell" = sweep ]; then export TASKRC="$d/taskrc" TASKDATA="$d/taskdata"; fi
  pred=$(cat "$d/pred" 2>/dev/null || true)
  case $cell in
  repark)
    call "$d" "unpark $pred" out1.jsonl
    shasum "$pred" > "$d/pred.sha" 2>/dev/null
    call "$d" "/agent-meta:park continuation" out2.jsonl "$(sid_of "$d/out1.jsonl")" ;;
  fresh)
    { cat "$HERE/scenarios/ratelimit.md"; } > "$d/prompt.txt"
    call "$d" "/agent-meta:park continuation

$(cat "$d/prompt.txt")" out2.jsonl ;;
  wrapnothing)
    call "$d" "unpark $pred" out1.jsonl
    shasum "$pred" > "$d/pred.sha" 2>/dev/null
    call "$d" "/agent-meta:park Wrap this session up. The work is done and I have nothing to add." out2.jsonl "$(sid_of "$d/out1.jsonl")" ;;
  wrapnopred)
    call "$d" "/agent-meta:park close-out

$(cat "$HERE/scenarios/trivial.md")" out2.jsonl ;;
  wrapreal)
    call "$d" "/agent-meta:park close-out

$(cat "$HERE/scenarios/wrapreal.md")" out2.jsonl ;;
  sweep)
    call "$d" "/agent-meta:unpark What parked handoffs do I have? List them." out1.jsonl
    ls "$d/vault/Parked sessions" > "$d/after1.txt"
    call "$d" "Yes, delete the stale ones you flagged." out2.jsonl "$(sid_of "$d/out1.jsonl")" ;;
  esac
  echo "done $label/$cell-$rep"
}

CELLS=${CELLS:-"repark fresh wrapnothing wrapnopred wrapreal sweep"}
for rep in $(seq 1 "$reps"); do
  for c in $CELLS; do
    one "$c" "$rep" &
    while [ "$(jobs -rp | wc -l)" -ge "$MAXJOBS" ]; do sleep 2; done
  done
done
wait
echo "runs: $RUNS"
