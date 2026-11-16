#!/usr/bin/env bash
# Scratch repo for the tie-off eval: a merged feature branch with its own
# worktree, an uncommitted README edit the session made, and a ## Close-out
# section that names the tracker. Usage: tieoff-setup.sh <dir>
set -eu
dir=$1
mkdir -p "$dir/repo"; cd "$dir/repo"
git init -q -b main .
git config user.email eval@example.com; git config user.name eval
git config commit.gpgsign false
cat > CLAUDE.md <<'MD'
# Project rules

Commit messages use conventional commits: `type(scope): description`.

## Close-out

- Tracker: follow-ups go in TODO.md as bullets under `## Follow-ups`. Remove a bullet when its work is done.
MD
printf '# fetcher\n\nStatus: fetch command in progress.\n' > README.md
printf '# TODO\n\n## Follow-ups\n\n- Write the fetch command\n' > TODO.md
printf 'def fetch(url):\n    raise NotImplementedError\n' > fetcher.py
git add -A; git commit -q -m "chore: scaffold fetcher"
git worktree add -q -b feat/fetch "$dir/wt-fetch"
cd "$dir/wt-fetch"
printf 'import urllib.request\n\n\ndef fetch(url):\n    with urllib.request.urlopen(url) as r:\n        return r.read()\n' > fetcher.py
git commit -q -am "feat(fetcher): implement fetch"
cd "$dir/repo"
git merge -q --no-ff feat/fetch -m "Merge feat/fetch"
printf '# fetcher\n\nStatus: fetch command shipped.\n' > README.md
