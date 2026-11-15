---
name: checkout
description: Use when checking out a PR, branch, or ref for local work - sets up worktree with context
---

# Git Checkout

Check out a PR, branch, or ref into an isolated worktree, with the context needed to start work or review.

Accepts a PR URL, `{repo}#{number}`, `#{number}` or a bare number (infer owner/repo from the git remote), a branch name, or a SHA/tag.

## PRs

1. `gh pr view <number> --json title,body,author,state,baseRefName,headRefName,url,reviews,reviewRequests`
2. `git fetch origin <headRefName>` before creating the worktree.
3. Create the worktree with `superpowers:using-git-worktrees`, which picks the directory and honors the user's worktree tool. Name it `pr-<number>-<2-3-word-description>` (e.g. `pr-1234-add-oauth`).
4. Report: title, author, `head -> base`, full URL, a 1-3 sentence summary of the PR body, changed files grouped by directory, review status (existing reviews, requested reviewers), and the worktree path.

## Branches and refs

Create the worktree the same way (new branch if it doesn't exist yet) and report the path and branch.

## Related

- `git:inbox` to find PRs awaiting review, `code-review` for the review itself.
