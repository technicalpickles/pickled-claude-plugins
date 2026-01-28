## Behavior: Codebase Maturity Signals

**Check codebase familiarity before major changes:**

1. Is there a CLAUDE.md? If not, the codebase may lack documented conventions
2. Are there tests in the relevant area?
3. How familiar is this part of the codebase?

**If no CLAUDE.md and user requests significant work:**

```
I notice there's no CLAUDE.md in this project yet. Before making
significant changes, it would help to capture project conventions.

Should I:
(A) Create a starter CLAUDE.md by exploring the codebase patterns
(B) Skip for now and proceed carefully
(C) You'll create one - just wait
```

**Why this matters:** Less documentation = more caution needed. CLAUDE.md helps Claude understand project conventions.
