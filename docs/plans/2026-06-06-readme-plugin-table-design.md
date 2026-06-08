# Design: generated plugin table for the root README

## Problem

The root `README.md` `## Plugins` section is hand-written prose with one subsection
per plugin. It is selective and goes stale:

- `marketplace.json` lists 17 plugins; the README documents 7.
- The README still documents `debugging-tools`, which is no longer in `marketplace.json`.
- Adding `sandbox-advisor` (PR #92) did not touch the root README at all.

The same drift affects two "Repository Structure" trees (root README and `CLAUDE.md`),
which each enumerate ~6 specific plugins.

There is no check that catches this, unlike `version-check.yml` which gates merge on
`marketplace.json` version drift.

## Goal

A plugin list that is complete, current, and **cannot silently drift** — backed by a
generator and a CI gate, mirroring the existing version-check pattern.

## Source of truth & data flow

`marketplace.json` is the canonical published list. The generator reads `.plugins[]`
from it (sorted alphabetically by name) so that:

- Only published plugins appear (the unpublished local dirs `debugging-tools` and
  `session-analyzer` are excluded automatically).
- External git-subdir plugins (`cq`, `petri-dish`) are included even though they have
  no local files.

For each plugin name the generator resolves a **description**, a **link**, and a
**skills** cell:

| Plugin kind | How identified | Description | Link | Skills |
|-------------|----------------|-------------|------|--------|
| Local | `.plugins[].source` is a string path `./plugins/<name>` | marketplace entry `.description` ?? `plugins/<name>/.claude-plugin/plugin.json` `.description` | `plugins/<name>` (its directory) | sorted dir names under `plugins/<name>/skills/`, `*-workspace` filtered |
| Remote (git-subdir, etc.) | `.plugins[].source` is an object | marketplace entry `.description` (required) | repo URL from `source.url`, `.git` stripped | a `[see repo](url)` link |

**Remote plugin descriptions live in their marketplace.json entry.** The marketplace
schema explicitly allows any plugin-manifest field (including `description`) on a plugin
entry, and the official docs show a `description` on a remote-source entry. This is the
one place this repo controls for a remote plugin, it keeps CI deterministic (no network
fetch at generate/check time), and it is where a maintainer naturally works when adding
a remote plugin. So adding `cq` and `petri-dish` descriptions to their marketplace
entries is part of this work.

The generator never reaches across the network and has no hardcoded plugin table — it is
fully driven by `marketplace.json` plus local `plugins/` contents. Remote plugins' skills
are not enumerated (no local dir, no reliable manifest field); their Skills cell is a
`[see repo](url)` pointer, which cannot drift, while their description stays current via
the marketplace entry.

### Skills resolution

Skills are the directory names under `plugins/<name>/skills/`. Helper skills whose
directory name ends in `-workspace` (e.g. `pull-feedback-workspace`,
`investigating-builds-workspace`) are **filtered out** — they are internal and not
meant for direct user invocation. A plugin with no remaining skills (hook-only plugins
such as `sandbox-advisor`, `stay-on-target`) renders an en-dash (`–`) in the Skills cell.

## README output

The `## Plugins` section becomes a single generated table delimited by marker comments,
so regeneration only rewrites the table body and never the surrounding prose:

```markdown
## Plugins

<!-- BEGIN GENERATED PLUGINS (run scripts/generate-plugin-table.sh) -->
| Plugin | Description | Skills |
|--------|-------------|--------|
| [cq](https://github.com/technicalpickles/cq) | Query past Claude Code sessions via the cq CLI (SQL over session transcripts) | [see repo](https://github.com/technicalpickles/cq) |
| [git](plugins/git) | Git workflow tools: commits, PRs, review inbox, checkout, and work triage | checkout, commit, inbox, pull-feedback, pull-request, push, triage, update |
| [sandbox-advisor](plugins/sandbox-advisor) | Turns Claude Code sandbox EPERMs into crisp re-run-unsandboxed guidance | – |
<!-- END GENERATED PLUGINS -->
```

The existing hand-written per-plugin prose subsections are removed and replaced by this
table. The link target for a local plugin is `plugins/<name>` (its directory, which
contains its own README); for a remote plugin it is the repo URL derived from
`source.url`.

## The script: `scripts/generate-plugin-table.sh`

Shell + `jq`, matching the style of the existing `scripts/*.sh`. Two modes, mirroring
`validate-plugin-versions.sh`:

- **Default (write):** regenerate the table and write it into `README.md` between the
  markers. Idempotent.
- **`--check`:** generate the expected table, compare against what is committed in
  `README.md`, and exit non-zero with a unified diff if they differ. Prints a hint to
  run the script without `--check`.

The script resolves the repo root relative to its own location so it works from any cwd.

### Wiring into bump-version

`scripts/bump-version.sh --auto` additionally invokes `generate-plugin-table.sh` (write
mode) after applying version bumps, so the existing per-PR version step regenerates the
table for free. The generator remains independently runnable.

## CI gate: `.github/workflows/plugin-list-check.yml`

A sibling of `version-check.yml`. On pull requests, checks out the branch, ensures `jq`
is available, and runs `scripts/generate-plugin-table.sh --check`. Fails the build (with
the diff in the log) when the committed README table does not match generated output.

## Encouraging correct behavior

Beyond the CI gate, three documentation touchpoints steer contributors toward the right
move and remove secondary drift sources:

1. **`CLAUDE.md` — Contributing:** the existing step that runs
   `./scripts/bump-version.sh --auto` gains a note that it also regenerates the README
   plugin table, and that `plugin-list-check.yml` gates merge on it.
2. **`CLAUDE.md` — Repository Structure tree:** stop enumerating 6 specific plugins;
   replace with a generic `plugins/<name>/` entry plus a pointer to the README Plugins
   section. (The enumerated tree is itself a stale list.)
3. **Root `README.md` — Repository Structure tree:** same de-enumeration, for the same
   reason.

(Out of band, the session memory note on pickled-claude-plugins versioning is updated to
record that the README plugin table is generated and CI-gated.)

## Non-goals

- No versions in the table (they live in `marketplace.json` and would be a fresh drift
  source).
- No network fetching at generate/check time. Remote plugin descriptions come from their
  marketplace.json entry; remote skills are a `see repo` link, not an enumeration.
- No restructuring of the rest of the README (Installation, Usage, Development sections
  are untouched beyond the Repository Structure tree).

## Verification

- `generate-plugin-table.sh` then `--check` exits 0 (idempotent, self-consistent).
- Hand-edit the README table, run `--check`, confirm non-zero + diff.
- Generated table contains all 17 marketplace plugins, excludes `debugging-tools` and
  `session-analyzer`, includes `cq`/`petri-dish`, omits `*-workspace` skills, shows `–`
  for hook-only plugins, and shows a `see repo` link for remote plugins' skills.
- A plugin that resolves no description (remote entry missing `description`, no local
  fallback) is a hard error in the generator, so a remote plugin can't be added without
  one.
- `bump-version.sh --auto` leaves the README table regenerated and consistent.
