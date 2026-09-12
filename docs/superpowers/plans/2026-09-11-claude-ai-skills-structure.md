# claude.ai Skills Structure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the existing `vault-capture` claude.ai-skill work out of a bare top-level `claude-ai-skills/` directory and into a repeatable, per-plugin convention (`plugins/{name}/claude-ai-skills/{skill}/`), backed by one shared build script and a porting guide.

**Architecture:** claude.ai-skill ports live inside the Claude Code plugin they're derived from, as a sibling to that plugin's `skills/`/`hooks/` directories. They are not Claude Code plugin skills themselves (no `plugin.json` entry, not installable via `/plugin`). One shared script at the repo root builds any plugin's port into an uploadable zip, replacing per-directory `build.sh` copies. A new doc explains the convention and gives a checklist for distinguishing a straight port (no tool/CLI/MCP/filesystem dependency in the source skill) from an adapted port (needs a capability-gap pass).

**Tech Stack:** Bash (`scripts/*.sh`, existing repo convention), Markdown (`SKILL.md`, docs), `zip`.

**Spec:** [`docs/superpowers/specs/2026-09-11-claude-ai-skills-structure-design.md`](../specs/2026-09-11-claude-ai-skills-structure-design.md)

## Global Constraints

- claude-ai-skill ports live at `plugins/{plugin-name}/claude-ai-skills/{skill-name}/`, never at a bare top-level `claude-ai-skills/`.
- They are never given a `.claude-plugin/plugin.json`, never added to `.claude-plugin/marketplace.json`, and never listed in the generated README plugin table.
- Build tooling is one shared script (`scripts/build-claude-ai-skill.sh`), not a script per plugin.
- Every zip must have `SKILL.md` at its root (not nested in a subfolder) — this is what claude.ai's uploader expects.
- Commits touching a plugin's claude-ai-skills work use that plugin's name as the conventional-commit scope (e.g. `feat(second-brain): ...`), same as any other change to that plugin.

---

### Task 1: Shared build script

**Files:**
- Create: `scripts/build-claude-ai-skill.sh`

**Interfaces:**
- Consumes: nothing (no earlier tasks)
- Produces: an executable `scripts/build-claude-ai-skill.sh <plugin> [skill-name ...]` that later tasks (Task 2) invoke directly as a shell command — no importable functions, just a CLI.

This replaces the old `claude-ai-skills/build.sh` (which zipped everything relative to itself) with a version that takes a plugin name and zips from `plugins/<plugin>/claude-ai-skills/<skill>/` into `plugins/<plugin>/claude-ai-skills/dist/<skill>.zip`. There's no existing automated test harness for the repo's `scripts/*.sh` utilities (`bump-version.sh`, `check-commit-scope.sh`, etc. are verified by direct invocation, not a test suite) — follow that same convention: verify by running the script against real fixture data in Task 2, once `vault-capture` exists at its new path.

- [ ] **Step 1: Write the script**

```bash
#!/usr/bin/env bash
#
# Packages a claude.ai Skill (a plugin's claude-ai-skills/{name}/ directory) into an
# uploadable zip. claude.ai Skills are a separate product from this repo's Claude Code
# plugins - see plugins/{plugin}/claude-ai-skills/ and docs/claude-ai-skill-porting.md.
#
# Usage:
#   ./scripts/build-claude-ai-skill.sh <plugin> [skill-name ...]
#   ./scripts/build-claude-ai-skill.sh second-brain                # build every skill under second-brain
#   ./scripts/build-claude-ai-skill.sh second-brain vault-capture  # build just one
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <plugin> [skill-name ...]" >&2
  exit 1
fi

plugin="$1"
shift
skills_root="$REPO_ROOT/plugins/$plugin/claude-ai-skills"

if [ ! -d "$skills_root" ]; then
  echo "error: no claude-ai-skills directory at plugins/$plugin/claude-ai-skills" >&2
  exit 1
fi

dist_dir="$skills_root/dist"
mkdir -p "$dist_dir"

skills=("$@")
if [ "${#skills[@]}" -eq 0 ]; then
  for dir in "$skills_root"/*/; do
    name="$(basename "$dir")"
    [ "$name" = "dist" ] && continue
    [ -f "$dir/SKILL.md" ] && skills+=("$name")
  done
fi

if [ "${#skills[@]}" -eq 0 ]; then
  echo "error: no skill directories with SKILL.md found under $skills_root" >&2
  exit 1
fi

for name in "${skills[@]}"; do
  skill_dir="$skills_root/$name"
  if [ ! -f "$skill_dir/SKILL.md" ]; then
    echo "skip: $name has no SKILL.md" >&2
    continue
  fi
  out="$dist_dir/$name.zip"
  rm -f "$out"
  (cd "$skill_dir" && zip -X -r "$out" . -x '.*')
  echo "built plugins/$plugin/claude-ai-skills/dist/$name.zip"
done
```

- [ ] **Step 2: Make it executable**

Run: `chmod +x scripts/build-claude-ai-skill.sh`

- [ ] **Step 3: Verify usage/error output before real fixtures exist**

Run: `./scripts/build-claude-ai-skill.sh`
Expected: prints `Usage: ./scripts/build-claude-ai-skill.sh <plugin> [skill-name ...]` to stderr and exits non-zero (no `plugins/` directory arg given).

Run: `./scripts/build-claude-ai-skill.sh does-not-exist`
Expected: prints `error: no claude-ai-skills directory at plugins/does-not-exist/claude-ai-skills` to stderr and exits non-zero.

- [ ] **Step 4: Run shellcheck**

Run: `shellcheck scripts/build-claude-ai-skill.sh`
Expected: no warnings. (If `shellcheck` isn't installed in the execution environment, skip this step — it's not part of this repo's CI today.)

- [ ] **Step 5: Commit**

```bash
git add scripts/build-claude-ai-skill.sh
git commit -m "feat(repo): add shared claude.ai-skill build script"
```

---

### Task 2: Migrate vault-capture into plugins/second-brain

**Files:**
- Create: `plugins/second-brain/claude-ai-skills/vault-capture/SKILL.md` (moved from `claude-ai-skills/vault-capture/SKILL.md`)
- Create: `plugins/second-brain/claude-ai-skills/vault-capture/references/jd-map.md` (moved from `claude-ai-skills/vault-capture/references/jd-map.md`)
- Delete: `claude-ai-skills/README.md`
- Delete: `claude-ai-skills/build.sh`
- Delete: `claude-ai-skills/dist/vault-capture.zip`
- Delete: `claude-ai-skills/vault-capture/SKILL.md`, `claude-ai-skills/vault-capture/references/jd-map.md` (via directory move)
- Modify: `.gitignore` (ignore build output)

**Interfaces:**
- Consumes: `scripts/build-claude-ai-skill.sh <plugin> [skill-name ...]` from Task 1
- Produces: `plugins/second-brain/claude-ai-skills/vault-capture/dist/vault-capture.zip` (gitignored build artifact) — nothing later depends on this programmatically, it's the deliverable a human uploads to claude.ai by hand

Both `claude-ai-skills/` (old, top-level, untracked) and `plugins/second-brain/` (existing, tracked) already exist in the working tree — this task only moves files and does not need to create the `plugins/second-brain/` directory itself.

- [ ] **Step 1: Move the skill directory**

```bash
mkdir -p plugins/second-brain/claude-ai-skills
git mv claude-ai-skills/vault-capture plugins/second-brain/claude-ai-skills/vault-capture 2>/dev/null || \
  mv claude-ai-skills/vault-capture plugins/second-brain/claude-ai-skills/vault-capture
```

(`claude-ai-skills/` was untracked before this plan, so plain `git status` after this step should show the new path as untracked, not staged as a rename — that's expected; `git mv` on untracked files falls back to a plain filesystem move, hence the `||` fallback.)

- [ ] **Step 2: Remove the old top-level directory's leftovers**

```bash
rm -f claude-ai-skills/README.md claude-ai-skills/build.sh
rm -rf claude-ai-skills/dist
rmdir claude-ai-skills/vault-capture 2>/dev/null || true
rmdir claude-ai-skills 2>/dev/null || true
```

- [ ] **Step 3: Verify the old directory is gone and the new one is in place**

Run: `test ! -e claude-ai-skills && echo "old dir gone"`
Expected: prints `old dir gone`

Run: `find plugins/second-brain/claude-ai-skills -type f | sort`
Expected:
```
plugins/second-brain/claude-ai-skills/vault-capture/SKILL.md
plugins/second-brain/claude-ai-skills/vault-capture/references/jd-map.md
```

- [ ] **Step 4: Ignore build output**

Add to `.gitignore` (append, keep existing entries above intact):

```gitignore

# claude.ai Skill build output (see docs/claude-ai-skill-porting.md)
plugins/*/claude-ai-skills/dist/
```

- [ ] **Step 5: Rebuild the zip via the shared script**

Run: `./scripts/build-claude-ai-skill.sh second-brain vault-capture`
Expected: prints `built plugins/second-brain/claude-ai-skills/dist/vault-capture.zip`

- [ ] **Step 6: Verify the zip shape**

Run: `unzip -l plugins/second-brain/claude-ai-skills/dist/vault-capture.zip`
Expected output includes, with `SKILL.md` at the zip root (not nested under `vault-capture/`):
```
SKILL.md
references/jd-map.md
```

- [ ] **Step 7: Commit**

```bash
git add plugins/second-brain/claude-ai-skills .gitignore
git status  # confirm claude-ai-skills/ (old top-level path) no longer appears at all
git commit -m "feat(second-brain): move vault-capture claude.ai skill into plugin directory"
```

---

### Task 3: Porting guide doc

**Files:**
- Create: `docs/claude-ai-skill-porting.md`

**Interfaces:**
- Consumes: nothing programmatically (references the script from Task 1 and the directory from Task 2 in prose/examples only)
- Produces: a doc that Task 4's `CLAUDE.md` pointer links to

- [ ] **Step 1: Write the doc**

```markdown
# claude.ai Skill Porting Guide

claude.ai Skills (Settings → Capabilities → Skills in the Claude chat app) are a
different product from this repo's Claude Code plugins. They're chat-only: no
filesystem, CLI, or MCP access, uploaded as a zip by hand instead of installed via
`/plugin install`. Some of this repo's Claude Code skills are worth porting there —
this doc covers where they live, how to build them, and what to watch for when
adapting one.

## Where they live

Each port lives inside the Claude Code plugin it's derived from, as a sibling to that
plugin's `skills/` and `hooks/` directories:

```
plugins/{plugin-name}/claude-ai-skills/{skill-name}/
  SKILL.md
  references/        # optional, same shape as Claude Code skills
```

A claude-ai-skills port is **not** a Claude Code plugin skill: it has no
`.claude-plugin/plugin.json` entry, isn't listed in `.claude-plugin/marketplace.json`,
and doesn't appear in the generated README plugin table. The only reason it's nested
inside `plugins/{name}/` is organizational — it sits next to the conventions it
mirrors, and a commit touching it naturally scopes to that plugin
(`feat(second-brain): add vault-capture claude.ai skill`), satisfying this repo's
existing commit-scope rule (see root `CLAUDE.md`'s Versioning section) with no
special-casing.

A plugin's `claude-ai-skills/` directory can hold more than one skill.

## Building

One shared script handles every plugin:

```bash
./scripts/build-claude-ai-skill.sh <plugin>                # build every skill under that plugin
./scripts/build-claude-ai-skill.sh <plugin> <skill-name>   # build just one
```

Output lands at `plugins/<plugin>/claude-ai-skills/dist/<skill-name>.zip`, gitignored.
`SKILL.md` sits at the zip root — that's the shape claude.ai's uploader expects.

## Uploading

claude.ai → Settings → Capabilities → Skills → upload the zip. Re-uploading the same
skill name replaces the previous version. There's no CLI for this; it's a manual step
after building.

## Porting checklist

When adapting a Claude Code skill into a claude.ai skill, start here:

**Does the source skill invoke tools, a CLI, MCP, or the filesystem?**

- **No** → straight port. The instructions carry over close to as-is. Review is
  lightweight — check the description still triggers correctly in a chat-only context,
  and that nothing in the body assumes Claude Code-specific mechanics (skill file
  paths, other installed plugins, etc.).
- **Yes** → adapted port. Do a capability-gap pass:
  1. Enumerate every capability the source skill relies on that claude.ai chat doesn't
     have (filesystem search, a CLI's dedup/validation logic, MCP calls, other
     installed skills it composes with).
  2. For each one, decide: disclose the gap plainly (tell the user this step can't be
     done and why), or find a chat-safe equivalent. Never fake it — don't have the
     skill claim to have deduplicated, searched, or validated something it structurally
     cannot.
  3. Check whether any reference data needs to be baked into `references/` because the
     source skill previously read it live from somewhere claude.ai can't reach (a
     vault's own `CLAUDE.md`, a database, another plugin's config). `vault-capture`'s
     `references/jd-map.md` is an example: it condenses the `pickled-knowledge` vault's
     Johnny Decimal layout, which the source `second-brain:capture` skill reads live
     from the vault's `CLAUDE.md` but a claude.ai skill can't.

**Either way**, the port goes through the full `superpowers:writing-skills` TDD process
(baseline subagent runs, rationalization tables) before being considered done. The
checklist above changes *what* needs adapting — it doesn't change whether the result
gets tested like any other skill.
```

- [ ] **Step 2: Commit**

```bash
git add docs/claude-ai-skill-porting.md
git commit -m "docs(repo): add claude.ai skill porting guide"
```

---

### Task 4: Root CLAUDE.md pointer

**Files:**
- Modify: `CLAUDE.md`

**Interfaces:**
- Consumes: `docs/claude-ai-skill-porting.md` (Task 3), `plugins/second-brain/claude-ai-skills/` (Task 2) as a concrete example
- Produces: nothing consumed by later tasks (this is the last task)

- [ ] **Step 1: Add a new section after "Plugin Internal Structure"**

In `CLAUDE.md`, insert a new section immediately after the "### Naming Gotchas" subsection ends and before `## Versioning` (i.e. right after the line containing `Slash-command wrappers pointing at skills are a legacy pattern from before skills were directly slash-callable.` and its trailing blank line):

```markdown
## claude.ai Skills

Some Claude Code skills are also worth porting to **claude.ai Skills** (the chat
product's own skill format — Settings → Capabilities → Skills, no filesystem/CLI/MCP
access, uploaded as a zip by hand). These ports live at
`plugins/{name}/claude-ai-skills/{skill}/`, colocated with the Claude Code plugin they
mirror, but they are **not** plugin skills — no `plugin.json` entry, no marketplace
entry, not part of the generated README table, and none of the versioning/commit-scope
mechanics below apply to their *content*. A commit touching one still uses that
plugin's name as its conventional-commit scope, same as any other change to the plugin.

→ Full details, the shared build script, and the straight-vs-adapted-port checklist:
[`docs/claude-ai-skill-porting.md`](docs/claude-ai-skill-porting.md)
```

- [ ] **Step 2: Add it to the Documentation list**

In the `## Documentation` section, add a bullet after the existing `docs/versioning.md` line:

```markdown
- [`docs/claude-ai-skill-porting.md`](docs/claude-ai-skill-porting.md) - How claude.ai Skills (a separate product from Claude Code plugins) are structured and built
```

- [ ] **Step 3: Verify the doc renders sensibly**

Run: `grep -n "claude-ai-skill-porting" CLAUDE.md`
Expected: two matches (the new section's link, and the Documentation list bullet).

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(repo): point CLAUDE.md at the claude.ai skill porting guide"
```

---

### Task 5: Final verification

**Files:** none (verification only)

**Interfaces:**
- Consumes: everything from Tasks 1-4
- Produces: nothing (terminal task)

- [ ] **Step 1: Confirm the old top-level directory is fully gone**

Run: `git status --porcelain | grep -c '^?? claude-ai-skills' || true`
Expected: `0`

- [ ] **Step 2: Confirm the new structure builds cleanly from a fresh clone's perspective**

Run: `git clean -ndx plugins/second-brain/claude-ai-skills` (dry run — lists what would be removed, does not delete)
Expected: only lists `plugins/second-brain/claude-ai-skills/dist/` (the gitignored build output), nothing else — confirms `SKILL.md` and `references/` are tracked, not accidentally gitignored.

- [ ] **Step 3: Confirm all commits from this plan are present**

Run: `git log --oneline -4`
Expected: four commits in this order (most recent first): the `CLAUDE.md` pointer commit, the porting-guide commit, the vault-capture migration commit, the build-script commit — on top of whatever was `HEAD` before this plan started.
