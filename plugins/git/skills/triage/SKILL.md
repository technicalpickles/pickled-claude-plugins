---
name: triage
description: Use when reviewing git state across worktrees, stashes, and branches - helps decide what to clean up, resume, or address
disable-model-invocation: true
---

# Git Triage

Inventory git work in progress (worktrees, stashes, local branches, uncommitted work) with enough context to decide what to resume, review, or clean up. The user can scope it to `worktrees`, `stash`, or `branches`; default is everything.

## For each item, find

- **Worktree:** branch, associated PR (`gh pr list --head <branch> --state all`) with state and a full URL, matching plan file under `docs/plans/`, uncommitted changes summarized by what they appear to do (infer from the diff, don't just count files), and unpushed commit subjects.
- **Stash:** age, source branch and whether it still exists, files touched.
- **Branch:** last commit age, PR and its state, whether the remote branch is gone. Judge "merged" by the PR state: squash merges don't show up in `git branch --merged`.

## Present

Group by worktrees, stashes, branches. Give every item a recommendation with its reason: resume (PR approved, needs a push), review (stash on a live branch, may be superseded), or safe to delete (PR merged, source branch gone, PR closed and remote deleted). End with a one-line count per group.

## Act

Offer the cleanup choices: individual items, "all safe-to-delete items", or nothing. **Never auto-delete.** For a bulk cleanup, list exactly what will be deleted and confirm before deleting anything.

## Related

- `git:checkout` to resume a worktree, `git:inbox` for PRs awaiting your review, `superpowers:finishing-a-development-branch` after finishing work.
