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

### Step 5: Present for approval

After resolving, show summary:

```markdown
## Conflict Resolution Summary

Merged `main` into `feature/my-branch`

### {filename}

**Your changes:** {1-2 sentence summary of what your commits did}
**Upstream changes:** {1-2 sentence summary of what upstream commits did}
**Resolution:** {1-2 sentence explanation of how resolved}

```diff
{Show key parts of the resolution}
```

---

[Repeat for each file]

---

**Verification:**
- [ ] No conflict markers remain
- [ ] File parses correctly (if applicable)

Does this resolution look correct?
(A) Yes, commit and push
(B) Let me review/adjust manually
(C) Show me more context on a specific file
```

Use AskUserQuestion with these options.

## Workflow: Verification & Completion

### Step 1: Verify no conflict markers

```bash
grep -rn "^<<<<<<< \|^=======$\|^>>>>>>> " {resolved_files}
```

If any found, resolution is incomplete - fix before proceeding.

### Step 2: Syntax verification (where practical)

| File Type | Check |
|-----------|-------|
| `.json` | `python -m json.tool {file} > /dev/null` |
| `.yaml`/`.yml` | `python -c "import yaml; yaml.safe_load(open('{file}'))"` |
| `.ts`/`.tsx` | `npx tsc --noEmit {file}` (if tsconfig exists) |
| `.py` | `python -m py_compile {file}` |

### Step 3: Commit and push

```bash
git add {resolved_files}
git commit -m "Merge {upstream} into {branch}

Resolved conflicts in:
$(for f in {resolved_files}; do echo "- $f"; done)"

git push
```

### Step 4: Report completion

```markdown
## Update Complete

Merged `{upstream}` into `{branch}`
Resolved {N} conflict(s):
- {file1}
- {file2}

Pushed to origin. PR should now be mergeable.
```

## Edge Cases

| Situation | Handling |
|-----------|----------|
| **Binary file conflicts** | Flag for manual resolution: "Binary file {file} has conflicts - please resolve manually" |
| **Submodule conflicts** | Flag with guidance: "Submodule {name} has conflicts. Usually: accept upstream version or update to specific commit" |
| **Someone else's branch** | Check with `gh pr view --json author -q '.author.login'`. If not current user, warn: "This is @{author}'s branch. They should be aware of changes. Continue?" |
| **Too complex to resolve** | Present what was understood, mark specific hunks as needing manual attention |
| **Merge already in progress** | Detect with `git status` showing "You have unmerged paths". Offer to continue or abort. |

## Quick Reference

| Command | Purpose |
|---------|---------|
| `git rev-parse --abbrev-ref @{upstream}` | Get tracking branch |
| `git merge --abort` | Cancel in-progress merge |
| `git diff --name-only --diff-filter=U` | List conflicted files |
| `git checkout --ours {file}` | Take your version entirely |
| `git checkout --theirs {file}` | Take upstream version entirely |
| `git show HEAD:{file}` | Your version of file |
| `git show MERGE_HEAD:{file}` | Upstream version of file |

## Related Skills

- `git:commit` - Commit practices (used after resolution)
- `git:pull-request` - Creating/updating PRs
- `git:triage` - Overview of work state