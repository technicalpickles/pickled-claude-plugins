---
description: Start an iterative CI fix session - investigate failures, apply fixes, and track progress until green
---

# Fix CI Failures

Start an iterative CI debugging session. This command helps you systematically investigate and fix CI failures through a structured workflow.

## Arguments

- **URL** (optional): Buildkite build URL to start investigating
- If no URL provided, infer from current branch

## Step 1: Determine the Build to Investigate

### If URL provided:

Parse the Buildkite URL to extract:
- Organization slug
- Pipeline slug
- Build number

### If no URL provided:

1. Get the current git branch:
   ```bash
   git branch --show-current
   ```

2. Identify the pipeline (check for common patterns):
   - Repository name often matches pipeline slug
   - Check `.buildkite/pipeline.yml` for pipeline hints

3. Find the latest build for this branch using MCP tools:
   ```javascript
   mcp__MCPProxy__call_tool('buildkite:list_builds', {
     org_slug: '<org>',
     pipeline_slug: '<pipeline>',
     branch: '<current-branch>',
     per_page: 5
   })
   ```

4. If no pipeline can be determined, ask the user for the Buildkite URL.

## Step 2: Capture Initial State

Record the starting point for this fix session:

- **Branch name**: Current git branch
- **PR number**: If applicable (check `gh pr view --json number`)
- **Build number**: The failing build we're investigating
- **Failure count**: Number of failed jobs

Announce this to the user:

> "Starting CI fix session for branch `<branch>` (Build #<number>). I see <N> failed jobs. Let me investigate."

### Optional: Create Tracking Document

For complex or multi-day debugging sessions, offer to create a tracking document:

> "Would you like me to create a tracking document for this CI fix session? Useful for multi-day debugging or handoff."

If yes, create `docs/plans/ci-fix-<branch-slug>.md` with this template:

```markdown
# CI Fix Workflow: <branch-name>

## Session: <YYYY-MM-DD>

### Initial State
- Branch: `<branch-name>`
- PR: #<pr-number>
- Latest failing build: <build-number> (<N> failures - <brief description>)

---

## Step 1: <Title>

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

---

## Tools Used

1. **MCP tools** - `buildkite:get_build`, `buildkite:list_annotations`
2. **git diff** - Compare branch changes with main
3. **Local commands** - <test runner, type checker, etc.>

---

## Next Steps

- [ ] <remaining items if session ends before green>
```

Update this document as you progress through the fix session.

## Step 3: Check Branch Freshness

**IMPORTANT**: Before diving into failures, ensure the branch is up to date with main.

1. Check if branch is behind main:
   ```bash
   git fetch origin main
   git rev-list --count HEAD..origin/main
   ```

2. If behind by more than 0 commits, recommend:
   > "Your branch is <N> commits behind main. Recommend merging main first to rule out stale code issues."

   Ask user if they want to:
   - Merge main now (handle conflicts if needed)
   - Skip and investigate current failures
   - The failures might already be fixed in main

## Step 4: Investigate Failures

Use the `working-with-buildkite-builds` skill workflows:

1. **Get build overview** with failed jobs only:
   ```javascript
   mcp__MCPProxy__call_tool('buildkite:get_build', {
     org_slug: '<org>',
     pipeline_slug: '<pipeline>',
     build_number: '<build>',
     detail_level: 'detailed',
     job_state: 'failed'
   })
   ```

2. **Check annotations** for summarized failures:
   ```javascript
   mcp__MCPProxy__call_tool('buildkite:list_annotations', {
     org_slug: '<org>',
     pipeline_slug: '<pipeline>',
     build_number: '<build>'
   })
   ```

3. **Get logs** for failed jobs to see actual errors

4. **Identify failure patterns**:
   - Test failures (RSpec, Jest, pytest, etc.)
   - Build/compilation errors
   - Linting/type checking errors
   - Infrastructure issues (Docker, dependencies)

## Step 5: Categorize and Plan Fixes

Group failures by type and plan the fix approach:

### Common Failure Categories

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
# Run affected tests
bin/rspec <spec_files>

# Type check modified files (if using Sorbet)
bin/srb tc <modified_files>

# Run pre-commit hooks
lefthook run pre-commit
# or: pre-commit run --files <modified_files>
```

### For JavaScript/TypeScript projects:
```bash
# Run affected tests
npm test -- <test_files>
# or: yarn test <test_files>

# Type check (if using TypeScript)
npx tsc --noEmit

# Lint
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

3. **Monitor the new build** using MCP tools:
   ```javascript
   mcp__MCPProxy__call_tool('buildkite:wait_for_build', {
     org_slug: '<org>',
     pipeline_slug: '<pipeline>',
     build_number: '<new-build>',
     timeout: 1800,
     poll_interval: 30
   })
   ```

4. **Report status** when build completes:
   - If passed: Celebrate and summarize what was fixed
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

4. **Track iterations** - after 3+ iterations, consider:
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

## Common Fix Patterns Reference

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

## Tool Reference

### Primary: MCP Tools
- `buildkite:get_build` - Build details and job list
- `buildkite:list_annotations` - Failure summaries
- `buildkite:get_logs` - Job output (requires job UUID, not step ID)
- `buildkite:wait_for_build` - Monitor until completion

### Secondary: CLI Tools
```bash
# bktide for quick checks
npx bktide build <org>/<pipeline>#<build>
npx bktide annotations <org>/<pipeline>#<build>

# git for branch comparison
git diff origin/main -- <path>
git log origin/main..HEAD --oneline
```

### Troubleshooting

**MCP tool returns "job not found":**
- You're using step ID from URL instead of job UUID
- Get job UUID from `get_build` with `detail_level: "detailed"`

**Build numbers must be strings** in MCP tools, not integers.

## Guidelines

- **Always verify locally** before pushing - saves CI cycles
- **One fix at a time** when possible - easier to identify what worked
- **Document as you go** - helps if session spans multiple days
- **Know when to stop** - sometimes fresh eyes or a different approach is needed
- **Check main first** - the issue might already be fixed there
