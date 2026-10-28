---
name: commit
description: Use when committing changes to git - provides best practices for staging, commit messages, signing, and handling hook failures
---

# Git Commit

Preferences and best practices for interacting with a git repository.

## git add

Stage the files you changed by path. `git add .` and `git add -A` sweep in whatever else is in the working tree, including files another session left there.

Ask before staging files that look like agent configuration or planning docs.

## git commit

PREFER writing the commit message to a file under `$TMPDIR`, named for what is being committed, then commit with `git commit -F "$TMPDIR/path-to-message.txt"`.

Use `-F` (`--file`), NEVER `-t` (`--template`). A template opens the message in an editor and git aborts if it comes back unchanged (`Aborting commit; you did not edit the message.`). Agent shells run with a no-op editor, so `-t` always aborts. The abort comes after pre-commit hooks run, so the failure looks like a hook problem. It isn't; don't reach for `--no-verify`.

Put any trailers your instructions require (e.g. `Co-Authored-By:`) at the end of the message file. Writing the message to a file first makes these easy to forget.

### scope the commit to your paths

PREFER `git commit -F <file> -- <path>...` over a bare `git commit`. A bare commit takes everything currently staged, including files another session or tool staged in the same working tree between your `git add` and your `git commit`. Naming the paths commits only what you meant to.

Path-limited commits take the working-tree version of those files, so skip `-- <path>` when you deliberately staged only some hunks of a file.

### signing

Commit signing is set up. Never bypass it (`--no-gpg-sign`, `-c commit.gpgsign=false`, switching keys). If signing fails, read the actual error and report it to the user; on a Mac with Automic Vault, the `automic-vault:automic-vault-credentials` skill covers agent signing failures.

## hooks

### pre-commit failures

When pre-commit checks fail, read what failed and fix it. Ask the user when the right fix is unclear.

DO NOT follow sorbet's autocorrection advice.
DO NOT skip verification without confirmation from the user.

### prepare-commit-msg and post-commit

`git: 'duet-prepare-commit-msg' is not a git command` comes from leftover git-duet hooks in `.git/hooks/` (we no longer use git-duet). Remove the hook files that call it.
