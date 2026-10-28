---
name: update
description: >-
  Use when a branch or PR has merge conflicts, is behind main, or needs upstream
  changes pulled in. Triggers on "resolve the merge conflicts", "there's a merge
  conflict on the PR, fix it", "rebase this PR on main", "catch this branch up
  with main", "update my branch". Fetches, merges the base branch (merge, not
  rebase), and resolves conflicts by reading the intent of both sides. Do NOT
  use for fast-forwarding a local main after a merge (just git pull).
---

# Git Update

Bring the current branch up to date with its base branch, resolving conflicts by intent.

- **Merge, never rebase**, to preserve history.
- Resolve autonomously, then **present the resolution for approval before committing**.

## Find the base branch

1. PR base: `gh pr view --json baseRefName -q .baseRefName`, merged as `origin/<base>`.
2. No PR: the remote's default branch, `git symbolic-ref --short refs/remotes/origin/HEAD`.
3. Neither works: ask which branch to merge from.

Don't use `@{upstream}`: for a pushed feature branch it is the branch's own remote copy, not the base, and agent branches often have no upstream at all.

## Merge

`git fetch origin`, then `git merge origin/<base> --no-edit`. Nothing to merge: say "already up to date" and stop. Clean merge: push and report how many commits came in.

If the branch belongs to someone else (`gh pr view --json author`), say so and confirm before pushing to it. If a merge is already in progress, offer to continue or abort it.

## Resolve conflicts

For each conflicted file, read both sides **and the commit messages that produced them** (`git log --format='%s%n%b' <merge-base>..HEAD -- <file>` and the same for `origin/<base>`) to learn what each side was trying to do. Then:

| Conflict | Resolution |
|---|---|
| Independent (different parts) | Keep both |
| Overlapping (same area, different purposes) | Re-apply this branch's intent on top of the newer approach, usually upstream's (if upstream refactored a function, adapt the branch's additions to the new shape) |
| Contradictory (mutually exclusive) | Don't auto-resolve; present both options with context |
| Binary, submodule, or too tangled | Flag for manual resolution with what you understood |

## Present, then commit

Before committing, show per file: what this branch's changes did, what upstream's did, how you resolved it, and the key hunk. Confirm no conflict markers remain and the file still parses. Ask: commit and push, adjust manually, or show more context.

On approval, commit only the resolved files with a message like `Merge origin/<base> into <branch>` listing them, push, and report the files resolved.
