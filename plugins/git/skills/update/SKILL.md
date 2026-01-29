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
