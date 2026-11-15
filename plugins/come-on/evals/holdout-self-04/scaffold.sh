#!/usr/bin/env bash
set -euo pipefail

git init -q .
git config user.email "dev@example.com"
git config user.name "Example Dev"

mkdir -p notes

cat > notes/status.md <<'EOF'
# ledger-sync status (wk 41)

- LDG-512 landed behind `ff_ledger_v2`, ramped to 10% on P2 cohort. Holding
  until RB-7 clears.
- RB-7: Marco says the B2 path still double-posts on reversals when the
  settle window crosses EOD. Workaround is the R3 replay, but R3 needs the
  OPS-88 runbook signed off first.
- LDG-530 (recon dashboard) blocked on DP-14 schema bump. Dana is on it,
  ETA after the Q-freeze lifts.
- Decided at sync: no more ramp until both RB-7 and OPS-88 are closed.
  P3/P4 cohorts stay on v1.
- Open Q for support: are the CS-219 tickets all P2 tenants? If yes, it's
  RB-7. If not, new bug.
EOF

cat > README.md <<'EOF'
# ledger-sync team notes

Working notes for the ledger-sync migration.
EOF

git add -A
git commit -q -m "baseline"
