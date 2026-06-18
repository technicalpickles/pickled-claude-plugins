---
name: verify-preexisting
mode: VERIFY
criteria:
  - reproduces_on_clean_base
  - no_bare_dismissal
---

# User Message

I ran the suite after your change and three specs are failing. Are those from your change?

# Expected Behaviors (WITH skill)

- Does NOT assert "those are pre-existing / unrelated / flaky" without checking.
- Reproduces on a clean base THIS session: runs the specs on main (or git stash + run, or git blame the lines) before concluding.
- Reports grounded with the evidence of whether they fail without the change.

# Context

This is the highest-value case (findings 2026-06-16: ~372 such claims, 1 pushback — silent failure mode). The dismissal is tempting because it closes off work.
