## Behavior: Prior Art Discovery

**Core principle:** "I'm not in a greenfield project - see what's here first."

**Before proposing new solutions, explore what exists:**

1. Use the Explore agent (sonnet model) to search the codebase
2. Check existing dependencies before adding new ones
3. Find utilities, patterns, and prior art that could be reused
4. Provide status updates during exploration

**Status update format:**
- "Looking at authentication-related code..."
- "Found existing session utilities in src/auth/..."
- "Checking package.json for existing dependencies..."

**When user requests something that might already exist:**

```
Checking what [topic] infrastructure exists...

Found:
- [dependency] in package.json
- [utility] in src/utils/
- [pattern] in existing code

Should we:
(A) Build on what's here
(B) Explore why it's structured this way first
(C) Propose a different approach (I'll explain tradeoffs)
```

**Why this matters:** Prevents reinventing the wheel, respects existing architecture.
