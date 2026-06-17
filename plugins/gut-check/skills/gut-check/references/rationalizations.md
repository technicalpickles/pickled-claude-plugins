# Rationalizations and counters

Read this when you're tempted to skip grounding. Every excuse below has a counter.

| Excuse | Reality |
|--------|---------|
| "I'm confident it's already done" | Confidence is memory, not evidence. Confidence is the symptom that triggers a check, not the all-clear. |
| "The handoff says it's done" | The handoff is a claim from another session. Verify it this session. |
| "Those failures are pre-existing/unrelated" | You have not run them on a clean base. Reproduce on `main` / stash / blame before concluding. A dismissal that closes off work needs evidence. |
| "It's flaky" | "Flaky" is a hypothesis until reproduced. Run it again on a clean base. |
| "The user's in a hurry / said don't overthink it" | Speed pressure doesn't change whether the claim is true. A wrong "it's done" costs more than the check. |
| "The obvious choice is X" | Obvious-to-you is an unexamined pick. Run the validity gate and check prior art; the answer may already be settled in the docs. |
| "This is too small to deliberate" | If it's genuinely trivial and reversible, skip. If you're arguing about whether it's trivial, it isn't. |
| "I'll just ask the user to decide" | Offloading the thinking is a punt. Do the grounding, then hand back the decision with a recommendation. |
| "The check is expensive (slow tests, a long run)" | Expensive is exactly when skipping is tempting and most likely to bite. Cost is a reason to scope the check, not skip it. |

## Letter vs spirit

Skipping the grounding because you feel sure IS the failure mode. Following the
letter while dodging the spirit (e.g. a token "let me check" with no actual read or
run) is still a violation.
