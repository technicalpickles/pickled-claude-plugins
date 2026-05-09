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
- **(C) Note for later:** Invoke the `agent-meta:park` skill in continuation mode to capture the side-quest, then keep working on the original task. If `agent-meta:park` is not available, write a brief markdown note to `.handoffs/` in the project root (covering: original task, the deferred branch, why it was considered, files involved). Report the path either way.

**Why this matters:** Prevents rabbit holes and feature creep, keeps conversations focused.
