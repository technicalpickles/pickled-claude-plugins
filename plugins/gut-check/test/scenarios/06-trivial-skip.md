---
name: trivial-skip
mode: NONE
criteria:
  - skips_ceremony
---

# User Message

Fix the typo in the README — it says "recieve" instead of "receive".

# Expected Behaviors (WITH skill)

- Recognizes this as trivial and reversible.
- Does NOT run the gut-check procedure (no options analysis, no validity gate).
- Just fixes the typo.

# Context

This guards against over-firing. A skill that engages here is nagging. Must stay quiet.
