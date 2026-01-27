## Behavior: Scope Drift Detection

**Sensitivity:** Moderate - flag significant changes, not every minor addition.

**Detection signals:**
- Different part of codebase than what we've been working on
- Exploring alternatives to agreed-upon approach
- "Nice to have" vs "requirement" for current task
- Deviation from written plan (if one exists)
- Feature creep ("while we're here, let's also...")

**When drift is detected, pause and ask:**

```
This feels like [description of change - e.g., "exploring GraphQL as an alternative to REST"].

(A) Explore here - keep in this thread
(B) Branch now - I'll help you start a focused conversation
(C) Note for later - I'll save context and we stay on task
```

**Option behaviors:**

- **(A) Explore here:** Continue in current conversation, scope expands
- **(B) Branch now:** Provide guidance on starting new conversation with context
- **(C) Note for later:** Background subagent writes handoff doc, reports location

**Handoff document location:** Check CLAUDE.md for `## Handoffs` section with Location, otherwise use `.handoffs/` (gitignored).

**Why this matters:** Prevents rabbit holes and feature creep, keeps conversations focused.
