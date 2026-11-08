#!/usr/bin/env bash
# Headless end-to-end check of park/unpark vault routing. Spends model tokens,
# so it is not part of the bats suite. Run it by hand before releasing a change
# to park, unpark, the park-vault hook, or the destination settings.
#
#   plugins/agent-meta/tests/e2e/park-vault.sh
#
# Each case runs `claude -p` against the plugins in this checkout (--plugin-dir),
# with a scratch vault and scratch working directory. Two kinds of assertion:
#   hook      the `Park vault:` line is in the session transcript. Deterministic.
#   behavior  the park file landed where the vault's CLAUDE.md says. Model-dependent,
#             so rerun a failure once before calling it a regression.
set -u

HERE=$(cd "$(dirname "$0")" && pwd)
PLUGINS=${PLUGINS_DIR:-$(cd "$HERE/../../.." && pwd)}
ROOT=$(mktemp -d "${TMPDIR:-/tmp}/park-e2e.XXXXXX")
VAULT="$ROOT/vault"
FAILS=0

mkdir -p "$VAULT/Parked sessions"
cat > "$VAULT/CLAUDE.md" <<'MD'
# Test vault

## Parking

Location: Parked sessions

Each park is one file named `YYYYMMDDHHMM [topic-slug].md`.
MD

check() { # description, command...
  desc=$1; shift
  if "$@" >/dev/null 2>&1; then echo "  ok   $desc"; else echo "  FAIL $desc"; FAILS=$((FAILS + 1)); fi
}

run_case() { # name, prompt, second-brain options json, [agent-meta options json]
  name=$1; prompt=$2; options=$3; meta=${4:-{\}}
  work="$ROOT/$name/work"; mkdir -p "$work"
  (cd "$work" && git init -q .)
  echo "{\"pluginConfigs\":{\"second-brain@inline\":{\"options\":$options},\"agent-meta@inline\":{\"options\":$meta}}}" > "$ROOT/$name/settings.json"
  (cd "$work" && timeout 300 claude -p "$prompt" \
      --plugin-dir "$PLUGINS/agent-meta" --plugin-dir "$PLUGINS/second-brain" \
      --settings "$ROOT/$name/settings.json" --add-dir "$VAULT" --permission-mode acceptEdits \
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

has_vault_line() { grep -q "Park vault: $VAULT" "$TRANSCRIPT"; }
no_vault_line() { ! grep -q "Park vault: /" "$TRANSCRIPT"; }
vault_park() { ls "$VAULT/Parked sessions/"[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]\ *"$1"*.md; }
absolute_unpark() { grep -q '^unpark "\{0,1\}/' "$(vault_park "$1" | head -1)"; }
local_park() { ls "$ROOT/$1/work/.parkinglot/"*.md; }
vault_empty() { [ -z "$(ls "$VAULT/Parked sessions" 2>/dev/null)" ]; }

SETTINGS_VAULT="{\"park_vault\":\"$VAULT\"}"
TAIL="Nothing is in progress. Just write a minimal park."

run_case slash "/agent-meta:park continuation, topic e2e-slash. $TAIL" "$SETTINGS_VAULT"
check "hook: Park vault line reached the model" has_vault_line
check "behavior: park file in vault with timestamp prefix" vault_park e2e-slash
check "behavior: unpark line uses an absolute path" absolute_unpark e2e-slash

run_case plain "Park this session as a continuation, topic e2e-plain. $TAIL" "$SETTINGS_VAULT"
check "hook: Park vault line reached the model" has_vault_line
check "behavior: park file in vault with timestamp prefix" vault_park e2e-plain

run_case unpark "Unpark the e2e-slash handoff and summarize it in one line." "$SETTINGS_VAULT"
check "hook: Park vault line reached the model" has_vault_line
check "behavior: the summary mentions the topic" grep -q "e2e-slash" "$ROOT/unpark/out.jsonl"

rm -rf "$VAULT/Parked sessions"/*
run_case off "/agent-meta:park continuation, topic e2e-off. $TAIL" "{\"park_in_vault\":false,\"park_vault\":\"$VAULT\"}"
check "hook: no Park vault line when park_in_vault is false" no_vault_line
check "behavior: vault stays empty" vault_empty
check "behavior: park lands in .parkinglot" local_park off

DEST="$ROOT/dest/work/destination.txt"
run_case dest "Park this session as a continuation, topic e2e-dest. $TAIL" "$SETTINGS_VAULT" "{\"destination\":\"printf %s {file} > $DEST\"}"
check "hook: destination setting reached the model as a Park destination line" grep -q "Park destination: printf" "$TRANSCRIPT"
check "behavior: the destination command ran with the park file path" grep -q "e2e-dest" "$DEST"

echo
echo "artifacts: $ROOT"
if [ "$FAILS" -eq 0 ]; then echo "all passed"; else echo "$FAILS failed"; exit 1; fi
