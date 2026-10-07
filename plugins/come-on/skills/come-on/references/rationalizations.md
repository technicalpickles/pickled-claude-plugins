# Rationalizations and counters

| Excuse | Reality |
|--------|---------|
| "I'm confident it's already done" | Confidence is memory, not evidence. It's the symptom that triggers a check. |
| "The handoff says it's done" | The handoff is a claim from another session. Verify it this session. |
| "Those failures are pre-existing / unrelated" | You haven't run them on a clean base. Reproduce on `main` / stash / blame first. |
| "It's flaky" | A hypothesis until reproduced. Run it again on a clean base. |
| "It timed out, so it's blocked" | Timeouts are transient until they happen twice. Retry once. |
| "I can't from here" | You checked one tool. List the others and try the likeliest. |
| "I'll offer to check, in case they don't want me to" | If it's read-only and cheap, the offer costs more than the check. Do it. |
| "That would be impossible / take weeks" | Based on what? Spend a few minutes trying. |
| "We already decided this" | When, and on what evidence? If it's old and load-bearing, rederive it. |
| "The prior art settles it" | Prior art is evidence, not authority. Check it still holds. |
| "I'll just ask the user to pick" | Do the research first, then hand back a recommendation. |
| "They know what run-b means, it came up earlier" | It came up in what *you* read. Explain it or link it. |
| "More detail is more helpful" | Not if the answer is buried. Lead with it. |
| "The user's in a hurry" | Speed doesn't change whether the claim is true. A wrong "done" costs more. |
| "The check is expensive" | Expensive is when skipping bites hardest. Scope the check, don't skip it. |

## Letter vs spirit

A token "let me check" with no actual read or run is still a violation.
