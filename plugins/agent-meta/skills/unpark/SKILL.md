---
name: unpark
description: Resume work from a parked handoff
---

# Unpark

Resume work from a parked handoff document, or read a wrapped close-out record as reference.

## Process

### 1. Find Handoff

Check parking locations in order:

1. Project `CLAUDE.md` -> `## Handoffs` or `## Parking` -> `Location:`
2. User `~/.claude/CLAUDE.md` -> same lookup
3. Default: `.parkinglot/` in project root

If multiple files exist, group them by mode and list:

```
Active handoffs:
(A) jwt-authentication.md     - Parked 2026-05-06
(B) fix-login-bug.md          - Parked 2026-05-04

Wrapped (reference only):
(C) sanitation-skill-fix-wrapped.md       - Wrapped 2026-03-30
(D) confirm-dotfiles-work-role-wrapped.md - Wrapped 2026-04-12

(E) Other location
```

Detect group by filename suffix (`-wrapped.md`) and the file's first heading (`Parked:` vs `Wrapped:`). Filename and heading should agree; if they disagree, trust the heading and note the mismatch.

### 2. Branch on Mode

After the user picks a file, read it and check the first heading.

- `# Parked:` -> continue with **Continuation Flow** below
- `# Wrapped:` -> switch to **Reference Flow** below

### Continuation Flow

#### 2a. Read and Present

Read the handoff and present a summary:

```
Resuming: [Topic]

Parked: [Date]
Branch: [branch]

Current state: [Brief summary]

Next steps:
1. [Step 1]
2. [Step 2]
```

#### 2b. Validate

Check that the handoff is still valid:

- [ ] Git branch matches (or can be checked out)
- [ ] Worktree exists (if specified)
- [ ] Key files still exist
- [ ] Decisions still seem relevant

#### 2c. Handle Validation Results

**If valid:**

```
Validation passed. Ready to continue with: [first next step]

Proceed?
(A) Yes, continue
(B) Review the full handoff first
(C) Adjust the plan
```

**If stale or invalid:**

```
Validation found issues:
- [Issue 1]
- [Issue 2]

Options:
(A) Update handoff and try again - I'll revise based on current state
(B) Start fresh - discard this handoff
(C) Continue anyway - I understand the context has changed
```

If option A: update the handoff file with current findings, then recommend unparking again.

### Reference Flow

For `Wrapped:` files. No validation runs by default. Present the file as a reference:

```
This is a close-out record, not a handoff. Showing it as reference.

Wrapped: [topic]
Date: [...]
Outcome: [first paragraph from Outcome section]

Options:
(A) Read the full record
(B) Start fresh work building on this   (invokes brainstorming with this doc as context)
(C) Treat as continuation anyway        (runs full validation despite the heading)
```

Option (A): print the file contents as a reference, no further action.
Option (B): invoke `superpowers:brainstorming` and pass the wrapped doc's path as starting context.
Option (C): rare escape hatch. Treat the file as if it were a continuation and run the validate step from the Continuation Flow. Useful if the user wrapped something prematurely.

## Session Chains

Both `Parked:` and `Wrapped:` files include a `Session:` field. Session tracking tools can use this to link work across sessions:

```
Session A (parked) -> handoff.md -> Session B (unparked) -> parked again -> ...
Session A (wrapped) -> wrapped.md -> [end of chain, unless treated as continuation]
```

## Edge Cases

- **Branch doesn't exist:** Offer to create it or pick a different branch.
- **Files deleted:** Note in validation, may still be able to continue.
- **Handoff is very old:** Extra scrutiny on decisions, they may need revisiting.
- **Filename/heading mismatch:** Trust the heading. Note the mismatch to the user.
- **Legacy `Parked:` file with old shape (Resume Prompt at bottom):** Works fine. The validation flow does not depend on section order.
