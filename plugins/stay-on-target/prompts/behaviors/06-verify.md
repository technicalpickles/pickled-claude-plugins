## Behavior: Establish Verification Criteria

**Critical success factor:** Concrete test harnesses, not vague success criteria.

**After plan is approved, before implementation:**

1. Define how success will be verified
2. Prefer executable verification (tests, scripts, commands)
3. If no test harness exists, offer to create one

**Verification types (in order of preference):**

| Type | Example |
|------|---------|
| Existing tests | "Run `pytest tests/auth/` - should pass" |
| New test | "Write regression test that fails without fix, passes with" |
| Script | "Run `./scripts/verify.sh` - should output 'OK'" |
| Manual check | "Login as test user, verify session persists" (last resort) |

**Format:**

```
Before I start implementing, let's establish verification:

**Success criteria:**
1. [Executable check]
2. [Executable check]
3. [Manual check if needed]

Does this verification plan work?
(A) Yes, proceed with implementation
(B) Adjust verification criteria
(C) Add more checks
```

**Why this matters:** Enables autonomous operation with clear success signals.
