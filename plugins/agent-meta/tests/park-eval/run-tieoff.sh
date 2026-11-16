#!/usr/bin/env bash
# Headless tie-off eval. Spends model tokens. Not part of CI.
#
#   run-tieoff.sh <label> <agent-meta-plugin-dir> [runs-dir]
#
# Runs the tieoff scenario twice: once asking for a close-out, once for a
# continuation. Score with: python3 -I score-tieoff.py <runs-dir>/<label>
set -u
label=$1; plugin=$(cd "$2" && pwd)
HERE=$(cd "$(dirname "$0")" && pwd)
RUNS=${3:-${TMPDIR:-/tmp}/park-eval-runs}

one() { # mode ask
  d="$RUNS/$label/$1"; rm -rf "$d"; mkdir -p "$d"
  "$HERE/tieoff-setup.sh" "$d"
  mkdir -p "$d/vault"; printf '# Scratch vault\n' > "$d/vault/CLAUDE.md"
  export SB_NOTE_VAULT="$d/vault"
  prompt="$(cat "$HERE/tieoff-scenario.md")

$2"
  (cd "$d/repo" && timeout 600 claude -p "$prompt" \
      --plugin-dir "$plugin" --add-dir "$d" --permission-mode acceptEdits \
      --allowedTools "Skill Read Write Edit Bash(git:*) Bash(ls:*) Bash(date:*) Bash(cat:*) Bash(mkdir:*) Bash(pwd:*)" \
      --output-format stream-json --verbose < /dev/null > "$d/out.jsonl" 2> "$d/err.txt")
  echo "done $label/$1"
}

one closeout "I've merged, /agent-meta:park. I'm done with this." &
one continuation "/agent-meta:park, I'm switching sessions and will keep going on this next time." &
wait
