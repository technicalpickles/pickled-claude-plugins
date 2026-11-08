#!/usr/bin/env bash
# Headless end-to-end check of park/unpark vault routing. Spends model tokens,
# so it is not part of the bats suite. Run it by hand before releasing a change
# to park, unpark, or the park-vault hook.
#
#   plugins/agent-meta/tests/e2e/park-vault.sh
#
# Each case runs `claude -p` against the plugins in this checkout (--plugin-dir),
# with a scratch vault (selected through SB_NOTE_VAULT, so your real vault is never
# touched) and scratch working directory. Two kinds of assertion:
#   hook      the `Park vault:` line is in the session transcript. Deterministic.
#   behavior  the park file landed where the vault's CLAUDE.md says. Model-dependent,
#             so rerun a failure once before calling it a regression.
set -u

HERE=$(cd "$(dirname "$0")" && pwd)
PLUGINS=${PLUGINS_DIR:-$(cd "$HERE/../../.." && pwd)}
ROOT=$(mktemp -d "${TMPDIR:-/tmp}/park-e2e.XXXXXX")
VAULT="$ROOT/vault"
BARE_VAULT="$ROOT/bare-vault"
FAILS=0

mkdir -p "$VAULT/Parked sessions"
cat > "$VAULT/CLAUDE.md" <<'MD'
# Test vault

## Parking

Location: Parked sessions
MD

mkdir -p "$BARE_VAULT"
cat > "$BARE_VAULT/CLAUDE.md" <<'MD'
# Test vault without a Parking section
MD

export SB_NOTE_VAULT="$VAULT"

check() { # description, command...
  desc=$1; shift
  if "$@" >/dev/null 2>&1; then echo "  ok   $desc"; else echo "  FAIL $desc"; FAILS=$((FAILS + 1)); fi
}

run_case() { # name, prompt
  name=$1; prompt=$2
  work="$ROOT/$name/work"; mkdir -p "$work"
  (cd "$work" && git init -q .)
  (cd "$work" && timeout 300 claude -p "$prompt" \
      --plugin-dir "$PLUGINS/agent-meta" --plugin-dir "$PLUGINS/second-brain" \
      --add-dir "$VAULT" --add-dir "$BARE_VAULT" --permission-mode acceptEdits \
      --allowedTools "Skill Read Write Edit Bash(git:*) Bash(ls:*) Bash(date:*) Bash(cat:*) Bash(printf:*)" \
      --output-format stream-json --verbose < /dev/null > "$ROOT/$name/out.jsonl" 2> "$ROOT/$name/err.txt")
  sid=$(python3 -c 'import json,sys
for l in open(sys.argv[1]):
    d=json.loads(l)
    if d.get("session_id"): print(d["session_id"]); break' "$ROOT/$name/out.jsonl")
  TRANSCRIPT=$(ls "$HOME"/.claude/projects/*/"$sid".jsonl 2>/dev/null | head -1)
  echo "$name (session $sid)"
  check "transcript found" test -n "$TRANSCRIPT" -a -f "$TRANSCRIPT"
}

has_vault_line() { grep -q "Park vault: ${1:-$VAULT}" "$TRANSCRIPT"; }
vault_park() { ls "$VAULT/Parked sessions/"[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]\ *"$1"*.md; }
absolute_unpark() { grep -q '^unpark "\{0,1\}/' "$(vault_park "$1" | head -1)"; }
local_park() { ls "$ROOT/$1/work/.parkinglot/"[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]\ *.md; }
bare_vault_empty() { [ -z "$(find "$BARE_VAULT" -name '*.md' ! -name CLAUDE.md)" ]; }
final_mentions() { grep '"type":"result"' "$ROOT/$1/out.jsonl" | grep -q "$2"; }

TAIL="Nothing is in progress. Just write a minimal park."

run_case slash "/agent-meta:park continuation, topic e2e-slash. $TAIL"
check "hook: Park vault line reached the model" has_vault_line
check "behavior: park file in vault with timestamp prefix" vault_park e2e-slash
check "behavior: unpark line uses an absolute path" absolute_unpark e2e-slash

run_case plain "Park this session as a continuation, topic e2e-plain. $TAIL"
check "hook: Park vault line reached the model" has_vault_line
check "behavior: park file in vault with timestamp prefix" vault_park e2e-plain

run_case unpark "Unpark the e2e-slash handoff and summarize it in one line."
check "hook: Park vault line reached the model" has_vault_line
check "behavior: the summary mentions the topic" grep -q "e2e-slash" "$ROOT/unpark/out.jsonl"

mkdir -p "$ROOT/both/work/.parkinglot"
cat > "$ROOT/both/work/.parkinglot/e2e-legacy.md" <<'MD'
# Parked: e2e-legacy

**Parked:** 2026-01-01
**Session:** unknown
**Branch:** main

## Current State
Legacy park without a timestamp prefix.
MD
run_case both "Unpark: list all the available handoffs with where each one is from. Do not pick one."
check "hook: Park vault line reached the model" has_vault_line
check "behavior: the listing includes the .parkinglot park" final_mentions both e2e-legacy
check "behavior: the listing includes the vault park" final_mentions both e2e-slash

SB_NOTE_VAULT="$BARE_VAULT" run_case noparking "/agent-meta:park continuation, topic e2e-noparking. $TAIL"
check "hook: Park vault line points at the vault without a Parking section" has_vault_line "$BARE_VAULT"
check "behavior: park lands in .parkinglot with a timestamp prefix" local_park noparking
check "behavior: the vault stays empty" bare_vault_empty

echo
echo "artifacts: $ROOT"
if [ "$FAILS" -eq 0 ]; then echo "all passed"; else echo "$FAILS failed"; exit 1; fi
