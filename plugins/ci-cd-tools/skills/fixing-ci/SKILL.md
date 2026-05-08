---
name: fixing-ci
description: Use when CI is failing on a branch, PR, or specific Buildkite build and the user wants to iteratively fix it through verify-locally → push → check → iterate. Strong signals: "fix CI", "make CI green", "CI is failing", "tests are failing in Buildkite", "iterate on this build", a Buildkite build URL paired with intent to push fixes, a PR with a red check the user wants to make green, or repeat-push debugging. Covers verify-fix-locally workflows (rspec, jest, lint, type checking before pushing), iteration tracking across multiple builds, and knowing when to step back after N failed attempts. Do NOT use for first-time investigation of a build (use `buildkite:investigating-builds` for "why did this fail" without a fix-and-push intent). Do NOT use for authoring pipeline YAML or adding pipeline steps (use `buildkite:developing-pipelines`). Do NOT use for GitHub Actions debugging or non-Buildkite CI. This skill drives the fix loop; investigation is delegated to `buildkite:investigating-builds`.
---

# Fixing CI

## Overview

This skill drives an iterative CI fix session: investigate the failure (via the Buildkite investigation skill), apply a fix, verify it locally, push, watch the new build, and iterate until green or until you've hit the iteration cap and need to step back.

The scope is the **fix loop only** — investigation is delegated to `buildkite:investigating-builds`, which already covers `bktide snapshot`, log reading, and failure-pattern recognition.

## When to Use

- You have a failing CI build and want to push fixes until it goes green
- You want to verify changes locally before each push (saves CI cycles)
- You're iterating on fixes across multiple builds and need to know when to step back

## When NOT to Use

- First-time "why did this fail" investigation with no fix-and-push intent → use `buildkite:investigating-builds` directly
- Authoring or modifying pipeline YAML → use `buildkite:developing-pipelines`
- GitHub Actions, CircleCI, or non-Buildkite CI

## Input Contract

The skill needs to know what to fix. Any one of these inputs is sufficient:

- **`build_url`** — A Buildkite build URL (e.g. `https://buildkite.com/org/pipeline/builds/123`)
- **`pr`** — A GitHub PR number (resolves to its latest failing build for that branch)
- **`branch`** — A git branch name (resolves to its open PR's latest failing build)

### Resolving inputs

If the caller provides one of the above, use it directly. Otherwise:

1. **From cwd**: read the current git branch (`git branch --show-current`), look for an open PR (`gh pr view --json number,headRefName`), find its latest failing build via the `buildkite:investigating-builds` skill's "Checking Current Branch/PR Status" workflow.
2. **If cwd doesn't resolve cleanly** (no branch, no open PR, no failing build): the caller (slash-command wrapper or workflow agent) is responsible for either asking the user or failing with a clear message. This skill assumes resolution is done before its loop starts.

## Step 1: Capture Initial State

Record the starting point:

- **Branch name**: Current git branch
- **PR number**: If applicable (`gh pr view --json number`)
- **Build number**: The failing build (from input contract)
- **Failure count**: Number of failed jobs (from a bktide snapshot of the build)

Announce:

> "Starting CI fix session for branch `<branch>` (Build #<number>). I see <N> failed jobs. Let me investigate."

## Step 2: Check Branch Freshness

Before diving into failures, check if the branch is up to date with main.

1. Check if behind main:
   ```bash
   git fetch origin main
   git rev-list --count HEAD..origin/main
   ```

2. If behind by more than 0 commits, the failures might already be fixed in main. Decide:
   - Merge main now (handle conflicts)
   - Skip and investigate current failures

In **autonomous mode** (e.g. invoked from a workflow agent), default to merging main if behind. The slash-command wrapper asks the user.

## Step 3: Investigate (Delegated)

Use the `buildkite:investigating-builds` skill to investigate the failing build. The skill's tool hierarchy applies: `bktide snapshot` first, then other bktide commands, then MCP tools as fallback.

After investigation, you should have:
- The failing job(s) and their logs
- A pattern category (test failure, lint, type error, lockfile, stale branch, infra, flake)
- Files likely involved

## Step 4: Categorize and Plan Fixes

Group failures by type:

| Category | Signs | Typical Fix |
|----------|-------|-------------|
| **Stale branch** | Tests pass on main | Merge main, resolve conflicts |
| **Gemfile.lock issues** | Checksum errors, missing gems | Regenerate from main (see references/common-fix-patterns.md) |
| **Test failures** | RSpec/Jest failures with stack traces | Fix the test or code |
| **Type errors** | Sorbet/TypeScript errors | Fix type annotations |
| **Lint errors** | Rubocop/ESLint failures | Auto-fix or manual fix |
| **Flaky tests** | Passes locally, fails in CI | Investigate timing/isolation; do NOT fix-and-push, surface as flake |

For each category, plan: what to fix, files involved, how to verify locally.

If the failure is `flake` or `infra` (CI runner/queue/dependencies), **stop**. Surface and exit. Don't push fixes for problems we don't understand.

## Step 5: Pre-Push Verification

**Always verify locally before pushing.** Saves CI cycles, catches misfires.

### Ruby/Rails projects
```bash
bin/rspec <spec_files>
bin/srb tc <modified_files>      # if using Sorbet
lefthook run pre-commit          # if using lefthook
pre-commit run --files <modified_files>  # if using pre-commit framework
```

### JavaScript/TypeScript projects
```bash
npm test -- <test_files>         # or: yarn test <test_files>
npx tsc --noEmit                 # if using TypeScript
npm run lint
```

### General
Run whatever the failing CI step ran. Check the failed job's command in the logs.

## Step 6: Push and Monitor

After local verification passes:

1. **Commit** with a message referencing the build:
   ```
   Fix <failure type> from build #<number>

   <brief description of what was wrong and how it was fixed>
   ```

2. **Push**:
   ```bash
   git push
   ```

3. **Monitor the new build** using the `buildkite:investigating-builds` skill's "Post-Push Monitoring" workflow.

4. On completion: pass → summarize and exit. Fail → go to Step 7.

## Step 7: Iterate if Still Failing

Compare with the previous build:
- Same failures → fix didn't work
- Different failures → progress, but new issues
- Fewer failures → partial progress

**Iteration cap: 3.** After 3 iterations without going green, **step back**. Don't keep trying. Exit with a summary covering:
- What was tried
- What's still failing
- A guess at why progress stalled (deeper architectural issue, branch too diverged, etc.)

Three iterations is a heuristic, not a hard rule — if iterations 1 and 2 made clear progress on different failures and iteration 3 is on the last remaining issue, one more attempt is reasonable. If the same failure persists across all three, stop.

## Step 8: Session Summary

When CI passes (or session ends), summarize:

- **Branch**: `<branch>`
- **Started**: Build #<first> (<N> failures)
- **Ended**: Build #<final> (passed / still failing)
- **Iterations**: <count>
- **Fixes applied**: brief list
- **Patterns encountered** and how each was resolved

## Common Fix Patterns

Detailed patterns for recurring issues (Gemfile.lock checksum, merge conflicts, year-boundary, test-helper changes) live in [references/common-fix-patterns.md](references/common-fix-patterns.md).

## Guidelines

- **Always verify locally** before pushing — saves CI cycles
- **One fix at a time** when possible — easier to identify what worked
- **Know when to stop** — sometimes fresh eyes are needed (3-iteration cap)
- **Check main first** — the issue might already be fixed there
