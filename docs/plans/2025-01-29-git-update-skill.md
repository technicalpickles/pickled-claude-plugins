# Design: `git:update` Skill

## Overview

A skill for updating your current branch with upstream changes, with intelligent conflict resolution.

**Trigger phrases:** "update", "sync", "pull in latest", "merge main"

**Primary use case:** You're the author of a PR that has conflicts and needs updating.

**Philosophy:**
- Merge (not rebase) to preserve history
- Resolve conflicts thoughtfully by understanding intent
- Show results for approval before committing

## Workflow: Detection & Merge

### Step 1: Detect upstream branch

```bash
# Try tracking branch first
git rev-parse --abbrev-ref @{upstream}

# If not set, check if we're on a PR branch
gh pr view --json baseRefName -q '.baseRefName'

# If neither, ask user
```

### Step 2: Fetch and merge

```bash
git fetch origin
git merge origin/{upstream-branch}
```

### Step 3: Branch on outcome

| Outcome | Action |
|---------|--------|
| Clean merge | Commit message auto-generated, push to remote |
| Conflicts | Proceed to conflict resolution workflow |
| Already up to date | Report "Already up to date" |

## Workflow: Conflict Resolution

### Step 1: Inventory conflicts

```bash
git diff --name-only --diff-filter=U
```

### Step 2: For each conflicted file, gather context

- Read the file with conflict markers
- Use `git log --oneline -5 -- {file}` on both branches to understand recent changes
- Look at the PR description or commit messages for intent

### Step 3: Analyze and resolve

For each conflict:

1. Identify what "ours" was trying to do (your branch's changes)
2. Identify what "theirs" was trying to do (upstream's changes)
3. Determine if changes are:
   - **Independent** - Both can coexist (e.g., different functions added)
   - **Overlapping** - Same area modified for different reasons (needs blending)
   - **Contradictory** - Mutually exclusive changes (needs decision)

4. Apply resolution, preferring to preserve both intents when possible

### Step 4: Present for approval

```markdown
## Conflict Resolution Summary

### file.ts
**Ours:** Added validation for email field
**Theirs:** Refactored form helpers to new pattern
**Resolution:** Applied your validation using the new helper pattern

[Show diff of resolved version]

---

Does this resolution look correct?
(A) Yes, commit and push
(B) Let me adjust manually
(C) Show me more context
```

## Workflow: Verification & Completion

### Step 1: Basic verification (always)

- Ensure no conflict markers remain (`<<<<<<<`, `=======`, `>>>>>>>`)
- Check files parse correctly (syntax check where tooling exists)

### Step 2: Contextual verification (when practical)

- If `package.json` was conflicted, run `npm install` / `yarn` to verify lockfile
- If tests are fast and local, offer to run them
- Check for any pre-commit hooks that would catch issues

### Step 3: Commit and push

```bash
git add {resolved-files}
git commit -m "Merge {upstream-branch} into {current-branch}

Resolved conflicts in:
- file1.ts
- file2.ts"

git push
```

### Step 4: Report completion

```markdown
## Update Complete

Merged `main` into `feature/my-branch`
Resolved 2 conflicts
Pushed to origin

PR should now be mergeable.
```

## Edge Cases

| Situation | Handling |
|-----------|----------|
| No upstream configured and no PR | Ask: "Update from which branch?" |
| Merge conflict too complex to auto-resolve | Present what was understood, offer manual resolution |
| Binary file conflicts | Flag for manual resolution, don't attempt auto |
| Submodule conflicts | Flag for manual resolution with guidance |
| User is on someone else's PR | Warn: "This is @{author}'s branch. Continue?" |
