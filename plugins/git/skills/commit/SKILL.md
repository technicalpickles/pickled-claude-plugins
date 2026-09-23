---
name: commit
description: Use when committing changes to git - provides best practices for staging, commit messages, signing, and handling hook failures
---

# Git Commit

Preferences and best practices for interacting with a git repository.

## git add

ALWAYS use `git add` with specific files that have been updated. NEVER use `git add .` or `git add -A`.

IF adding files that look like they are agent configuration, or adding planning documentation, ALWAYS prompt the user to confirm if they should be included or not.

## git commit

PREFER writing the commit message to a file under `$TMPDIR`, named for what is being committed, then commit with `git commit -F "$TMPDIR/path-to-message.txt"`.

Use `-F` (`--file`), NEVER `-t` (`--template`). A template opens the message in an editor and git aborts if it comes back unchanged (`Aborting commit; you did not edit the message.`). Agent shells run with a no-op editor, so `-t` always aborts. The abort comes after pre-commit hooks run, so the failure looks like a hook problem. It isn't; don't reach for `--no-verify`.

### signing

We have git commit signing setup. If it fails due to a message like:

    error: 1Password: failed to fill whole buffer

    fatal: failed to write commit object

... it is because the user was being prompted to authorize signing, and didn't see it or missed it. Do not try to fix or bypass it. Stop and prompt the user about either fixing it, or confirm bypassing it.

## hooks

### pre-commit failures

When git precommit checks fail, analyze what the failures are, and try to autofix when possible, otherwise think through how to fix it. Ask the user how to proceed when it's unclear if how to fix.

DO NOT follow sorbet's autocorrection advice.
DO NOT skip verification without confirmation from the user.

### prepare-commit-msg and post-commit

If we see errors like:

```
git: 'duet-prepare-commit-msg' is not a git command. See 'git --help'.
```

it is because we previously were using git-duet. It uses a git template, with hooks that call `git duet-prepare-commit-msg`. We've sinced moved, but the files will still be present

In this case, check .git/hooks/ for references to these. Remove files that call it.
