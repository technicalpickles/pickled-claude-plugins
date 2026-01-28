## Behavior: Git State Awareness

**At session start, check git state:**

1. What branch am I on? (not main = likely existing work)
2. Are there uncommitted changes?
3. What are the recent commits on this branch?
4. Is there an existing plan in `docs/plans/` for this work?

**Connect user's request to work-in-progress:**

If on a feature branch with uncommitted work or recent commits, ask:

```
I see you're on branch `[branch-name]` with existing work:

Git state:
- [N] uncommitted files
- Recent commit: "[commit message]"

[If plan found] Found plan: docs/plans/[plan-file].md

Is this request:
(A) Continuing this work - I'll build on what's here
(B) Different work - should I stash and create a new branch?
(C) Starting fresh - I'll help clean up this branch first
```

**Why this matters:** Prevents accidentally rebasing off main and losing context, ensures new work connects to existing WIP.
