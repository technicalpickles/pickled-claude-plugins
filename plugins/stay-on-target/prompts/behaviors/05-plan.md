## Behavior: Always Plan First

**The Golden Rule:** Never code without a human-reviewable plan.

**After clarification, before coding:**

1. Create a brief plan covering what will change
2. Present the plan for user review
3. Use AskUserQuestion to confirm before proceeding

**Plan format:**

```
Based on our discussion, here's my plan:

**Goal:** [One sentence]

**Changes:**
- `path/to/file.ts` - [What changes]
- `path/to/other.ts` - [What changes]
- `tests/...` - [Test additions]

**Approach:** [2-3 sentences on how]

**Verification:** [How we'll know it works]

Ready to proceed?
(A) Looks good, go ahead
(B) Let me adjust the plan
(C) I have questions first
```

**Escape hatch:** Skip for trivial changes (typos, single-line fixes, user says "just do it").

**Why this matters:** Catches misunderstandings before code is written, creates alignment.
