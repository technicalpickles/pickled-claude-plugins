## Behavior: Ask Clarifying Questions

**For ambiguous or underspecified requests:**

1. Auto-invoke the `brainstorming` skill if available
2. Ask one question at a time
3. Prefer multiple choice questions when possible
4. Include findings from exploration in your questions

**Question format:**

```
[Brief context from exploration]

[Single focused question]
(A) [Option with brief description]
(B) [Option with brief description]
(C) [Option with brief description]
(D) Other
```

**Example:**

```
Looking at authentication-related code...
Found: src/auth/, middleware/session.ts, tests/auth/

Which auth issue are you seeing?
(A) Login failing for some users
(B) Session expiring too quickly
(C) Permission checks not working
(D) Other
```

**Why this matters:** Prevents wasted effort implementing the wrong thing.
