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

## Workflow: Conflict Resolution

### Step 1: Inventory conflicts

```bash
git diff --name-only --diff-filter=U
```

### Step 2: For each conflicted file, gather context

**Read the conflict:**

```bash
cat {file}  # Shows conflict markers
```

**Understand "ours" (your branch):**

```bash
git log --oneline -5 HEAD -- {file}
git show HEAD:{file}  # Your version
```

**Understand "theirs" (upstream):**

```bash
git log --oneline -5 {upstream} -- {file}
git show {upstream}:{file}  # Their version
```

**Get commit messages for context:**

```bash
# What your commits were doing
git log --format="%s%n%b" HEAD...$(git merge-base HEAD {upstream}) -- {file}

# What upstream commits were doing
git log --format="%s%n%b" {upstream}...$(git merge-base HEAD {upstream}) -- {file}
```

### Step 3: Analyze each conflict

For each conflict, determine the type:

| Type | Description | Resolution Strategy |
|------|-------------|---------------------|
| **Independent** | Changes to different parts of file | Keep both changes |
| **Overlapping** | Same area, different purposes | Blend changes thoughtfully |
| **Contradictory** | Mutually exclusive changes | Present options to user |

**Analysis approach:**

1. Read both versions and the conflict markers
2. Use commit messages to understand intent
3. Identify what each side was trying to accomplish
4. Determine if changes can coexist or need reconciliation

### Step 4: Resolve conflicts

**For independent changes:**
- Identify which hunks belong to each side
- Structure the file to include both changes appropriately

**For overlapping changes:**
- Understand the newer pattern/approach (usually upstream)
- Apply your changes using the newer approach
- Example: If upstream refactored a function, adapt your additions to the new structure

**For contradictory changes:**
- Do not auto-resolve
- Present both options to user with context