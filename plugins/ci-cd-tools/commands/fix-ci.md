---
description: Start an iterative CI fix session — resolve the input (build / PR / branch / cwd), then run the `fixing-ci` skill loop until CI is green or you've hit the iteration cap.
---

# Fix CI Failures

Iteratively fix a failing Buildkite CI run. This command resolves what to fix, then loads the `ci-cd-tools:fixing-ci` skill to drive the loop (verify locally → push → check → iterate).

## Arguments

- **URL** (optional): Buildkite build URL to start with
- If no URL provided, infer from current branch / open PR

## Step 1: Resolve the Input

Determine the build to fix using this priority order:

1. **URL argument** provided → use it directly. The `bktide snapshot` tool parses any Buildkite URL.
2. **No URL, current git branch has an open PR** → resolve via `gh pr view --json number,headRefName`, then find the latest failing build for that branch using the `buildkite:investigating-builds` skill's "Checking Current Branch/PR Status" workflow.
3. **No URL, current branch but no PR** → ask the user for either the build URL or the PR number.
4. **Detached HEAD or no clear branch** → ask the user.

Once resolved, you have one of: `build_url`, `pr` number, or `branch` name.

## Step 2: Optional Tracking Document

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

## Iteration 1: <Title>

**Build:** <number> (<status>)
**Failures:** <count> (<pattern description>)

**Root cause:**
<1-2 sentences>

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

If no, skip and proceed.

## Step 3: Run the Fix Loop

Use the `ci-cd-tools:fixing-ci` skill, passing the resolved input from Step 1. The skill drives the loop: branch-freshness check → delegate investigation → categorize → verify locally → push → monitor → iterate (max 3 iterations).

When the skill returns (CI green, iteration cap hit, or classified as flake/infra/unknown), surface the session summary to the user.
