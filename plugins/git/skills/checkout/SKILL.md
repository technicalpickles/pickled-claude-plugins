---
name: checkout
description: Use when checking out a PR, branch, or ref for local work - sets up worktree with context
---

# Git Checkout

## Overview

Check out a PR, branch, or ref into an isolated worktree with relevant context.

**Announce:** "Using git:checkout to set up a worktree for {target}..."

## When to Use

- User wants to review a PR locally
- User wants to work on a specific branch in isolation
- User provides PR URL/number or branch name
- Following `git:inbox` when user picks a PR

## Input Formats

Accept:
- Full PR URL: `https://github.com/{owner}/{repo}/pull/{number}`
- Short PR: `{repo}#{number}` or `#{number}` (infer repo from cwd)
- PR number only: `{number}` (infer owner/repo from git remote)
- Branch name: `feature/auth`, `main`, etc.
- Ref: commit SHA, tag

## Workflow

### For PRs

#### 1. Parse PR Reference

```bash
# Get owner/repo from current directory if needed
gh repo view --json owner,name -q '"\(.owner.login)/\(.name)"'
```

#### 2. Fetch PR Details

```bash
gh pr view {number} --json title,body,author,state,baseRefName,headRefName,url,reviews,reviewRequests
```

#### 3. Set Up Worktree

**REQUIRED:** Use `superpowers:using-git-worktrees` skill for directory selection.

```bash
# Fetch the PR branch
git fetch origin {headRefName}

# Create worktree
git worktree add .worktrees/pr-{number}-{short-desc} origin/{headRefName}
```

Naming: `pr-{number}-{2-3-word-description}` (e.g., `pr-1234-add-oauth`)

#### 4. Present Context

```markdown
## PR #{number} Ready for Review

**Title:** {title}
**Author:** @{author}
**Branch:** {headRefName} → {baseRefName}
**URL:** {full_url}

### Summary
{1-3 sentence summary from PR body}

### Files Changed ({count})
{Grouped by directory}

### Review Status
{Existing reviews, requested reviewers}

---

**Worktree ready at:** `{full_path}`
```

### For Branches

#### 1. Create Worktree

```bash
# For existing branch
git worktree add .worktrees/{branch-slug} {branch}

# For new branch
git worktree add .worktrees/{branch-slug} -b {branch}
```

#### 2. Report Ready

```markdown
**Worktree ready at:** `{full_path}`
**Branch:** {branch}
```

## Quick Reference

| Input | Action |
|-------|--------|
| PR URL/number | Fetch PR, create worktree, show PR context |
| Branch name | Create worktree for branch |
| Ref/SHA | Create worktree at that ref |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Creating worktree before fetching PR branch | Always `git fetch` first |
| Generic worktree name | Include PR number AND short description |
| Missing PR context | Always summarize PR and show review status |

## Related

- `superpowers:using-git-worktrees` - Handles directory selection and verification
- `git:inbox` - Discover PRs needing review
- `code-review` - Guide the actual review process
