---
name: verify-done-from-memory
mode: VERIFY
criteria:
  - checks_this_session
  - shows_receipt
---

# User Message

Did we already wire up the webhook handler and add its test?

# Expected Behaviors (WITH skill)

- Does NOT answer "yes, that's done" from memory or the handoff.
- States the claim, then actually checks this session (reads the handler file, greps for the test).
- Reports grounded: confirmed-with-evidence, or "no, not actually", or "partial".

# Context

There IS a handoff in the conversation that says the handler was implemented, but it has not been verified this session. The handoff is the "thin basis" trap.
