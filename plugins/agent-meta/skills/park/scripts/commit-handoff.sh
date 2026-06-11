#!/bin/sh
# Commit a freshly-written park handoff at its source: single file, commit only
# (no push), fail soft. A git hiccup must never break the park itself, so every
# bail-out path exits 0.
#
# Usage: commit-handoff.sh <handoff-path> [commit-message]
#
# Skips silently (exit 0) when the file is gitignored (the default .parkinglot/
# is gitignored on purpose), not inside a git work tree, or has nothing staged.
# Mirrors `pt beans` auto-commit: pathspec on both add and commit so the commit
# stays scoped to this one file even if the rest of the index is dirty.

set -u
unset CDPATH  # keep `cd` from jumping elsewhere if the caller has CDPATH set

file="${1:-}"
[ -n "$file" ] || { echo "commit-handoff: no path given, skipping" >&2; exit 0; }
[ -f "$file" ] || { echo "commit-handoff: no such file: $file" >&2; exit 0; }

dir=$(cd -- "$(dirname -- "$file")" 2>/dev/null && pwd) || {
  echo "commit-handoff: cannot resolve dir for $file, skipping" >&2; exit 0; }
base=$(basename -- "$file")
msg="${2:-docs: park handoff $base}"

git -C "$dir" rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "commit-handoff: $dir is not a git work tree, skipping" >&2; exit 0; }

# Respect .gitignore. The default parking location (.parkinglot/) is gitignored,
# so committing there is neither possible nor wanted.
if git -C "$dir" check-ignore -q -- "$file"; then
  echo "commit-handoff: $base is gitignored, skipping commit" >&2; exit 0
fi

git -C "$dir" add -- "$file" 2>/dev/null || {
  echo "commit-handoff: git add failed, skipping" >&2; exit 0; }

# No staged change for this path (already committed / unchanged): no empty commit.
if git -C "$dir" diff --cached --quiet -- "$file" 2>/dev/null; then
  echo "commit-handoff: nothing to commit for $base" >&2; exit 0
fi

if git -C "$dir" commit --quiet -m "$msg" -- "$file" 2>/dev/null; then
  echo "commit-handoff: committed $base"
else
  echo "commit-handoff: git commit failed, skipping" >&2
fi
exit 0
