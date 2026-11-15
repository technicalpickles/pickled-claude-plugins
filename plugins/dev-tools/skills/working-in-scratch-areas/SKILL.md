---
name: working-in-scratch-areas
description: Use when creating one-off scripts, debug tools, analysis reports, or temporary documentation - ensures work is saved to persistent .scratch areas with proper documentation, organization, and executable patterns
---

# Working in Scratch Areas

One-off scripts, debug tools, analysis notes, and reports worth keeping go in the repo's `.scratch/` area, not in the repo tree or a temp dir. `.scratch` is a symlink from the repo root to a per-repo directory under a central scratch-areas root, so the files outlive the checkout and never get committed. (The session scratchpad the harness provides is still the place for throwaway intermediates nobody will look at again.)

## Setup

`test -L .scratch` tells you whether the repo has one. If not:

1. Find the areas root: a "Scratch Areas" line in `~/.claude/CLAUDE.md` (the setup script reads it), else ask the user. Suggest `~/workspace/scratch-areas`, or a `scratch-areas/` dir next to the repo.
2. From the repo root, run this skill's `scripts/setup-scratch-area.sh [--areas-root PATH] [--save-to-claude-md]`. It creates the repo's area, the `.scratch` symlink, and a README from the template. Skip `--save-to-claude-md` when `~/.claude/CLAUDE.md` is generated from dotfiles; add the line to its source instead.
3. Make sure `.scratch` is gitignored, globally (`git config --global core.excludesfile`) or in the project `.gitignore`.

## Rules

- **Always a topic subdirectory** (`.scratch/database-debug/`), never the `.scratch/` root. Reuse a relevant existing subdirectory if there is one (ask if unsure). Each subdirectory gets a `README.md`: what's in it, what investigation spawned it, how the files relate.
- **Every file starts with a header**: purpose, date created, and what it was used for. Scripts also need a shebang.
- Make scripts executable with this skill's `scripts/make-executable <file>` (checks for a shebang; approved once instead of per-file `chmod`), then run them directly (`./.scratch/sub/script.sh`), not through an interpreter, so allow-lists match.
- **Never delete; document instead.** When a file is done, add a `[RESOLVED - <date>]` header: how it was used, what it found, why it's kept.
- **Never commit scratch files.** Stage explicit paths, never `git add .` or `git add -A`.

If `~/workspace/pickled-scratch-area/` exists, it holds one-time migration and test tools for scratch areas.
