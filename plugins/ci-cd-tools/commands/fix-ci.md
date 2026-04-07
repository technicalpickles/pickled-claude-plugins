---
description: Start an iterative CI fix session - investigate failures, apply fixes, and track progress until green
---

# Fix CI Failures

Start an iterative CI debugging session. Systematically investigate and fix CI failures through a structured loop: investigate → fix → verify locally → push → check → iterate.

This command orchestrates the debugging loop. For all Buildkite interaction (fetching builds, reading logs, monitoring), use the `investigating-builds` skill workflows and tool hierarchy.

## Arguments

- **URL** (optional): Buildkite build URL to start investigating
- If no URL provided, infer from current branch

## Step 1: Determine the Build

### If URL provided:

Use the `investigating-builds` skill's "Investigating a Build from URL" workflow — `bktide snapshot` parses any Buildkite URL automatically.

### If no URL provided:

1. Get the current git branch:
   ```bash
   git branch --show-current
   ```

2. Identify the pipeline:
   - Repository name often matches pipeline slug
   - Check `.buildkite/pipeline.yml` for pipeline hints

3. Use the skill's "Checking Current Branch/PR Status" workflow to find the latest build for this branch.

4. If no pipeline can be determined, ask the user for the Buildkite URL.

## Step 2: Capture Initial State

Record the starting point:

- **Branch name**: Current git branch
- **PR number**: If applicable (`gh pr view --json number`)
- **Build number**: The failing build
- **Failure count**: Number of **root** failures (see Step 2.1)

Announce to the user:

> "Starting CI fix session for branch `<branch>` (Build #<number>). I see <N> root failures (<M> dependent steps blocked). Let me investigate."

### Step 2.1: Filter to Root Failures

**CRITICAL: Do this immediately after getting build data.** Most CI builds have 1-3 root failures and hundreds of dependent BROKEN steps. Finding the root failures fast is the whole game.

After running `bktide snapshot`, categorize steps by state:

```bash
jq -r '.steps[].state' manifest.json | sort | uniq -c | sort -rn
```

**Only these are real failures:**
- Steps with state `FINISHED` (or `FAILED`) AND a non-zero `exit_status`

**These are NOT failures — do not count or investigate them:**
- **BROKEN** — Downstream dependencies that never ran. They auto-fix when the root failure is fixed.
- **RUNNING** — Still in progress. Not failures.
- **WAITING** / **SCHEDULED** — Haven't started yet.
- **CANCELED** — Manually or automatically canceled.

Find actual root failures:
```bash
jq -r '.steps[] | select((.state == "FINISHED" or .state == "FAILED") and .exit_status != null and .exit_status != 0) | "\(.label) (exit \(.exit_status))"' manifest.json
```

**Example:** A build reports "466 steps: 43 passed, 397 failed, 361 running" — but filtering reveals 1 actual failure (codeownership validation) and 396 BROKEN dependents. Fix the 1 root cause and everything else passes.

### Optional: Create Tracking Document

For complex or multi-day debugging sessions, offer to create a tracking document:

> "Would you like me to create a tracking document for this CI fix session? Useful for multi-day debugging or handoff."

If yes, create `docs/plans/ci-fix-<branch-slug>.md`:

```markdown
# CI Fix Workflow: <branch-name>

## Session: <YYYY-MM-DD>

### Initial State
- Branch: `<branch-name>`
- PR: #<pr-number>
- Latest failing build: <build-number> (<N> failures - <brief description>)

---

## Iteration 1: <Title>

**Build:** <number> (<status>)
**Failures:** <count> (<pattern description>)

**Root cause:**
<1-2 sentences explaining why this failed>

**Fix:**
<Code changes or commands>

**Verification:**
\`\`\`bash
<local verification commands>
\`\`\`

**Commit:** `<sha>` - "<message>"
**Next build:** <number>

---

## Summary of Issues Fixed

| Build | Issue | Root Cause | Fix |
|-------|-------|------------|-----|
| <num> | <issue> | <cause> | <fix> |

## Next Steps

- [ ] <remaining items if session ends before green>
```

## Step 3: Check Branch Freshness

**IMPORTANT**: Before diving into failures, check if the branch is up to date with main.

1. Check if branch is behind main:
   ```bash
   git fetch origin main
   git rev-list --count HEAD..origin/main
   ```

2. If behind by more than 0 commits:
   > "Your branch is <N> commits behind main. Recommend merging main first to rule out stale code issues."

   Ask user if they want to:
   - Merge main now (handle conflicts if needed)
   - Skip and investigate current failures
   - The failures might already be fixed in main

## Step 4: Investigate Root Failures

Use the `investigating-builds` skill to investigate. The skill's tool hierarchy applies: `bktide snapshot` first, then other bktide commands, then MCP tools as fallback.

**Investigate only the root failures identified in Step 2.1.** Ignore BROKEN and RUNNING steps entirely — they are noise. Read the logs for each root failure and identify patterns:
- Test failures (RSpec, Jest, pytest, etc.)
- Build/compilation errors
- Linting/type checking errors
- Infrastructure issues (Docker, dependencies)

## Step 5: Categorize and Plan Fixes

Group failures by type and plan the fix approach:

| Category | Signs | Typical Fix |
|----------|-------|-------------|
| **Stale branch** | Tests pass on main | Merge main, resolve conflicts |
| **Gemfile.lock issues** | Checksum errors, missing gems | Regenerate from main |
| **Test failures** | RSpec/Jest failures with stack traces | Fix the test or code |
| **Type errors** | Sorbet/TypeScript errors | Fix type annotations |
| **Lint errors** | Rubocop/ESLint failures | Auto-fix or manual fix |
| **Flaky tests** | Passes locally, fails in CI | Investigate timing/isolation |

For each failure category, outline:
1. What needs to be fixed
2. Files likely involved
3. How to verify locally before pushing

## Step 6: Pre-Push Verification

**Before pushing any fix**, verify locally:

### For Ruby/Rails projects:
```bash
bin/rspec <spec_files>
bin/srb tc <modified_files>      # if using Sorbet
lefthook run pre-commit          # or: pre-commit run --files <modified_files>
```

### For JavaScript/TypeScript projects:
```bash
npm test -- <test_files>         # or: yarn test <test_files>
npx tsc --noEmit                 # if using TypeScript
npm run lint
```

### General:
```bash
# Run whatever CI runs locally if possible
# Check the failed job's command in the logs
```

## Step 7: Push and Monitor

After local verification passes:

1. **Commit the fix** with a descriptive message referencing the build:
   ```
   Fix <failure type> from build #<number>

   <brief description of what was wrong and how it was fixed>
   ```

2. **Push the changes**:
   ```bash
   git push
   ```

3. **Monitor the new build** using the `investigating-builds` skill's "Post-Push Monitoring" workflow.

4. **Report status** when build completes:
   - If passed: Summarize what was fixed
   - If failed: Go to Step 8

## Step 8: Iterate if Still Failing

If the new build still has failures:

1. **Compare with previous build**:
   - Same failures? Fix didn't work
   - Different failures? Progress, but new issues
   - Fewer failures? Partial progress

2. **Document the iteration**:
   > "Build #<new> still failing with <N> failures (was <M>). <same/different> failure pattern."

3. **Return to Step 4** with the new build number

4. **Track iterations** — after 3+ iterations, consider:
   - Is there a deeper architectural issue?
   - Should we get another pair of eyes?
   - Is the branch too diverged from main?

## Step 9: Session Summary

When CI finally passes (or session ends), summarize:

```markdown
## CI Fix Session Summary

**Branch:** <branch-name>
**Started:** Build #<first-build> (<N> failures)
**Ended:** Build #<final-build> (passed / still failing)
**Iterations:** <count>

### Fixes Applied
1. <Fix 1 description>
2. <Fix 2 description>

### Patterns Encountered
- <Pattern 1 and how it was resolved>

### Lessons Learned
- <Any insights for future debugging>
```

## Common Fix Patterns

### Gemfile.lock Checksum Issues

**Symptom:** `Your lockfile has an empty CHECKSUMS entry for "<gem>"`

**Fix:**
```bash
rm Gemfile.lock
git checkout origin/main -- Gemfile.lock
bundle lock
bundle install  # verify
git add Gemfile.lock
git commit -m "Regenerate Gemfile.lock with proper checksums"
```

### Merge Conflicts Blocking Push

**Fix:**
```bash
git stash push -m "WIP changes"
git fetch origin main
git merge origin/main --no-edit
# Resolve conflicts
git add <conflicted-files>
git commit
git stash pop
# Resolve any conflicts from stash
```

### Test Matcher/Helper Changes Breaking Tests

**Diagnosis:** Compare with main to see what changed:
```bash
git diff origin/main -- spec/support/
git diff origin/main -- test/helpers/
```

**Fix:** Often need to restore original behavior for non-target tests while adding new behavior for new tests.

### Year Boundary Test Failures

**Symptom:** Tests involving dates fail around new year

**Fix:** Look for hardcoded years or date assumptions in tests.

## Guidelines

- **Always verify locally** before pushing — saves CI cycles
- **One fix at a time** when possible — easier to identify what worked
- **Document as you go** — helps if session spans multiple days
- **Know when to stop** — sometimes fresh eyes or a different approach is needed
- **Check main first** — the issue might already be fixed there
