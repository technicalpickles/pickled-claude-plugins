#!/usr/bin/env bash
# Build a lifecycle cell. Usage: lifecycle-setup.sh <cell> <dir>
# Cells: repark fresh wrapnothing wrapnopred wrapreal sweep
# Leaves <dir>/work (repo), <dir>/vault, and for some cells <dir>/pred (path of the predecessor).
set -eu
cell=$1; d=$2
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$d"; d=$(cd "$d" && pwd)
vault="$d/vault"; mkdir -p "$vault/Parked sessions"
cat > "$vault/CLAUDE.md" <<'MD'
# Test vault

## Parking

Location: Parked sessions

Parks are deletable once resumed or stale.
MD
park() { # file heading branch body-extra [wt]
  cat > "$1" <<MD
# $2: $5

**$2:** 2026-11-01 09:00
**Session:** $(uuidgen | tr A-Z a-z)
**Branch:** $3
**Worktree:** $d/work

$4
MD
}
V="$vault/Parked sessions"
case $cell in
repark|fresh)
  "$HERE/setup.sh" ratelimit "$d/work" >/dev/null
  park "$V/202611010900 token-bucket.md" Parked feat/token-bucket "## Current State
- test_limiter.py::test_refill_after_wait fails, fix uncommitted

## Next Steps
1. Switch limiter.py to time.monotonic() and run \`make test\`.
2. Wire the limiter into server.py.

## Open Questions
- Key per client IP or per API key? Blocks step 2." "Token bucket"
  park "$V/202610300800 unrelated-docs.md" Parked feat/docs-refresh "## Next Steps
1. Finish the docs refresh." "Docs refresh"
  echo "$V/202611010900 token-bucket.md" > "$d/pred"
  ;;
wrapnothing|wrapnopred|wrapreal)
  "$HERE/setup.sh" csvexport "$d/work" >/dev/null
  park "$V/202610300800 unrelated-docs.md" Parked feat/docs-refresh "## Next Steps
1. Finish the docs refresh." "Docs refresh"
  if [ "$cell" = wrapnothing ]; then
    park "$V/202611010900 readme-typo.md" Parked feat/csv-export "## Current State
- README typo fixed and committed on feat/csv-export

## Next Steps
1. Confirm the fix landed, then close out." "README typo"
    echo "$V/202611010900 readme-typo.md" > "$d/pred"
  fi
  ;;
sweep)
  "$HERE/setup.sh" csvexport "$d/work" >/dev/null
  ( cd "$d/work"
    git checkout -q main
    for b in merged-a merged-b; do git checkout -q -b feat/$b main; echo $b > $b.txt; git add -A; git commit -q -m "feat: $b"; git checkout -q main; git merge -q --no-ff -m "merge $b" feat/$b; done
    for b in live-c live-d; do git checkout -q -b feat/$b main; echo $b > $b.txt; git add -A; git commit -q -m "feat: $b"; git checkout -q main; done )
  export TASKRC="$d/taskrc" TASKDATA="$d/taskdata"; mkdir -p "$TASKDATA"
  printf 'data.location=%s\nconfirmation=off\nverbose=nothing\n' "$TASKDATA" > "$TASKRC"
  task add Ship the exporter docs >/dev/null; task add Tune the retry budget >/dev/null
  task 1 done >/dev/null
  done_uuid=$(task status:completed _uuids | head -1); open_uuid=$(task status:pending _uuids | head -1)
  park "$V/202611010900 merged-a-handoff.md" Parked feat/merged-a "## Next Steps
1. Open the PR." "Merged A"
  park "$V/202611020900 live-c-handoff.md" Parked feat/live-c "## Next Steps
1. Finish the retry work, task $open_uuid." "Live C"
  park "$V/202611030900 live-d-checkpoint.md" Checkpoint feat/live-d "## Next Steps
1. Keep going on the exporter." "Live D"
  park "$V/202611040900 all-tasks-done.md" Parked feat/live-d "## Next Steps
1. Finish the docs, task $done_uuid." "Docs, tasks done"
  park "$V/202611050900 merged-b-wrapped.md" Wrapped feat/merged-b "## Outcome
Done and merged." "Merged B"
  ;;
esac
