---
name: update
description: Use when updating your branch with upstream changes - fetches, merges, and intelligently resolves conflicts
---

# Git Update

## Overview

Update your current branch with changes from the upstream branch, intelligently resolving conflicts when they occur.

**Announce:** "Using git:update to sync your branch with upstream..."

**Philosophy:**
- Merge (not rebase) to preserve history
- Understand intent behind conflicting changes
- Resolve autonomously, present for approval before committing

## When to Use

- User says "update", "sync", "pull in latest", "merge main"
- PR has conflicts that need resolving
- Branch is behind upstream and needs updating
- User wants to incorporate recent changes from main/master

## Workflow: Detect Upstream

### Step 1: Try tracking branch

```bash
git rev-parse --abbrev-ref @{upstream} 2>/dev/null
```

If this succeeds, use the result (e.g., `origin/main`).

### Step 2: Fall back to PR base branch

If no tracking branch:

```bash
gh pr view --json baseRefName -q '.baseRefName' 2>/dev/null
```

If this succeeds, use `origin/{result}`.

### Step 3: Ask user if neither works

If both fail, use AskUserQuestion:

```
I couldn't detect an upstream branch for this branch.

Which branch should I merge from?
(A) main
(B) master
(C) Other - I'll specify
```

## Workflow: Fetch and Merge

### Step 1: Fetch latest

```bash
git fetch origin
```

### Step 2: Check if update needed

```bash
git rev-list --count HEAD..{upstream}
```

If count is 0, report "Already up to date with {upstream}" and stop.

### Step 3: Attempt merge

```bash
git merge {upstream} --no-edit
```

### Step 4: Branch on result

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 0 | Clean merge | Push and report success |
| 1 | Conflicts | Proceed to conflict resolution |

**On clean merge:**

```bash
git push
```

Report:

```markdown
## Update Complete

Merged `{upstream}` into `{current-branch}`
{N} commits pulled in
Pushed to origin
```