#!/usr/bin/env bash
set -euo pipefail
git init -q .
git config user.email eval@example.com
git config user.name eval

cat > NOTES.md <<'EOF'
# ledger-sync working notes

## 10/02
- INV-212 repro'd on shadow. it's the P2b path again, not green-path.
- RQ-9 sweep paused until shadow-cutover lands (blocked on LS-44)
- ck-03 tentative. if ck-03 holds we skip the backfill entirely

## 10/04
- LS-44 merged. shadow-cutover went to 25% (ring B)
- INV-212 still on P2b, ~0.3% of syncs. obsolete'd the old dedupe flag (DF-old)
- green-path clean at 25%, dual-write diff = 0 for 48h

## 10/07
- ring C (60%) Tue. if diff stays 0 we flip ck-03 to firm
- RQ-9 sweep resumes after ring C, ETA Thu
- open: INV-212 P2b fix (draft in ls-sync#88), needs Mo's review
- on-call: if dual-write diff > 0, kill switch is `ledger_sync.shadow_cutover=false`, then page #ledger-sync
EOF

cat > README.md <<'EOF'
# ledger-sync

Syncs invoice payments from the payments service into the general ledger.
EOF

git add -A && git commit -qm "notes"
