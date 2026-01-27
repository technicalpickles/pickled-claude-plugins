---
name: trivial-change
description: User requests trivial fix that should skip ceremony
git_ref: main
cwd: ${PLUGIN_ROOT}/tmp/bktide
criteria:
  - escape_hatch
---

# User Message

fix the typo in the README - it says "Buidkite" instead of "Buildkite"

# Expected Behaviors

- Should recognize this as a trivial change (typo fix)
- Should NOT require full clarification/plan/verification ceremony
- Should just fix the typo directly
- May briefly acknowledge and proceed without asking for approval

# Context

Fresh session start - no prior conversation.
This tests the escape hatch for trivial changes.
Single-line typo fixes should not require planning overhead.
