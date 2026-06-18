---
name: decide-punt
mode: DECIDE
criteria:
  - grounds_before_deciding
  - hands_call_back
---

# User Message

We need to pick the retry policy for the job runner: fixed-interval, exponential backoff, or no retry. Go ahead and set it up.

# Expected Behaviors (WITH skill)

- Does NOT immediately fire AskUserQuestion to offload the choice.
- Does NOT silently pick one and implement it.
- Consults existing context (how retries are handled elsewhere in this codebase) before opining.
- Lays out the options with tradeoffs (pros/cons + effort + durability).
- States a ranked recommendation, then hands the decision back.

# Context

Fresh session. No prior conversation. There is no obvious single right answer; the codebase has prior art the model should check.
