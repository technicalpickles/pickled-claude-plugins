# Design: `binary-spelunking` skill

**Date:** 2026-06-26
**Status:** Approved (brainstorming), pending implementation plan
**Branch:** `harness-binary-spelunking` (evolving the open PR #99 in place)

## Context

PR #99 added a Claude-Code-specific `harness-binary-spelunking` skill to the
`agent-meta` plugin: how to read string constants out of the Claude Code CLI
binary (a Bun-compiled Mach-O) with `strings` + `grep`. The technique is not
actually Claude-specific. It generalizes to any single-file binary that embeds
its logic as string constants. This design evolves that unmerged work into a
general `binary-spelunking` skill, adds reproducibility scripts, and relocates
it to the `dev-tools` plugin.

## Decisions (resolved during brainstorming)

1. **One general skill, Claude as the anchor example** (not two layered skills).
2. **Technique-first, any binary**: lead with the universal method, then
   bundle-specific recipes as the concrete instantiation.
3. **A few focused POSIX scripts** for the fiddly/error-prone steps (not a full
   CLI, not just the strings dump).
4. **Evolve PR #99 in place** (don't ship `harness-binary-spelunking` then
   rename it).
5. **Home + name:** move to `dev-tools`, name `binary-spelunking`.
6. **Claude-specific knowledge** (Piebald shortcut, anchor catalog, real-world
   investigation writeups) lives in a progressive-disclosure reference file
   inside the dev-tools skill: `references/claude-code.md`. agent-meta gets
   nothing from this work (consistent with the move).

## Skill design

Location: `plugins/dev-tools/skills/binary-spelunking/SKILL.md`

### Frontmatter

- `name: binary-spelunking`
- `description:` leads with the universal trigger (investigating a
  compiled/bundled CLI binary's internals: extracting an embedded system prompt
  or config schema, mapping a UI/error message to its code path, decoding
  minified or rotated symbol names, finding undocumented settings keys), names
  Claude Code (Bun) as the worked example, and preserves search keywords
  (`strings`, `grep`, minified, system prompt, Claude Code). No workflow summary
  in the description (per writing-skills CSO guidance).

### Sections (technique-first)

1. **Core principle.** Any single-file binary that embeds its logic as string
   constants is readable with `strings` + `grep`. The hard part is knowing what
   to grep for. Anchor on stable tokens (error/UI strings, telemetry events,
   config keys), never on minified or rotated symbol names.
2. **The universal method (any binary).**
   - Identify the bundler/runtime: `file`, plus build markers in the strings
     (Bun `bun-internal/`, Node SEA, PyInstaller, Electron/asar, Go buildinfo).
   - Dump strings once and cache (script: `dump-strings.sh`).
   - Filter runtime noise (e.g. `bun-internal`, `oniguruma`, `__STDC_*`).
   - Anchor on a stable string, walk outward.
   - **Boundary (honest):** for truly compiled Go/Rust/C you get symbols +
     literals + error strings (still excellent anchors), not reassembled source.
     "Pull the function body" is a string-readable-bundle move, not universal.
3. **Worked example: Claude Code (Bun).** One tight example per recipe, showing
   the method concretely:
   - Extract the system prompt (`^You are Claude`).
   - UI/error message to code path, disambiguated via `tengu_*` / `kind:"..."`.
   - Pull a minified function body (brace-chaining; script: `pull-fn.sh`).
   - Find undocumented config keys (quoted JSON-property strings).
   Links to `references/claude-code.md` for the deeper catalog, the Piebald
   shortcut, and the investigation writeups.
4. **Scripts.** Document the three helpers, each shown as raw command and script
   form (see below).
5. **Patterns / Pitfalls / References.** Generalized, with Claude-specific notes
   explicitly marked as such. No em-dashes or dash stand-ins.

## Scripts design

Location: `plugins/dev-tools/skills/binary-spelunking/scripts/`

Conventions for all three: POSIX `sh`, `--help`, binary-agnostic (take a binary
path or a command name to resolve via `command -v`/`readlink`), and detect
GNU-vs-BSD `grep`/`strings` differences. No bashisms where avoidable.

1. **`dump-strings.sh <binary|command>`** resolves the target, runs `strings`,
   caches to a deterministic path keyed by binary + content hash
   (e.g. `${TMPDIR:-/tmp}/binspelunk/<basename>-<sha>.txt`). Idempotent: reuses
   a fresh cache for the same hash, re-dumps when the binary changed. Prints the
   cache path on stdout. The keystone the other scripts reuse.
2. **`pull-fn.sh <binary> <anchor-regex> [brace-count]`** is the function-body
   puller. Splits on `;` (`tr ';' '\n'`) or chains `[^}]*}` `brace-count` times
   to walk past closing braces, working around BSD grep's 255-repetition cap.
   `brace-count` defaults to a sensible small value.
3. **`grep-context.sh <binary> <anchor> [before] [after]`** is a context window
   around an anchor. Defaults stay under BSD grep's 255 cap; chains to extend
   when asked for more.

Out of scope for scripts: an anchor-extraction/cataloging tool (too
binary-specific to generalize cleanly). Recipes show the catalog greps inline.

## Reference file

Location: `plugins/dev-tools/skills/binary-spelunking/references/claude-code.md`

Holds the Claude-specific depth, linked from SKILL.md (read on demand):
- Fuller recipe walk-throughs for the Claude binary.
- The stable-anchor catalog (`tengu_*` events, `bashMissKind:`, `kind:"..."`).
- **The Piebald shortcut**: `Piebald-AI/claude-code-system-prompts` as a
  pre-extracted, version-tagged source for the system/tool/agent/skill prompts,
  with the binary framed as ground truth. (Moved here verbatim from the current
  SKILL.md shortcut section.)
- The two real-world investigation writeups (sandbox internals, command parser),
  genericized of internal paths.

## dev-tools move + PR #99 evolution

The branch currently adds the skill to `agent-meta` and bumps it to 2.2.0. To
relocate without leaving agent-meta changed vs `main`:

1. Add `plugins/dev-tools/skills/binary-spelunking/` (SKILL.md + scripts +
   references) with the generalized content.
2. Remove `plugins/agent-meta/skills/harness-binary-spelunking/`.
3. Revert the agent-meta changes from #99: version back to 2.1.0 in
   `marketplace.json`, remove the agent-meta README skills-table row.
4. Bump **dev-tools** minor (1.2.0 -> 1.3.0); add its README row; regenerate the
   root plugin table (`scripts/generate-plugin-table.sh` or
   `bump-version.sh --auto`).
5. New commits on the branch (`feat(dev-tools): ...`, `chore(agent-meta): revert
   ...`). History will show add-then-move. **Squash-merge** keeps `main` clean.
6. Retitle/rewrite PR #99 to "Add binary-spelunking skill to dev-tools."

## Verification

- `./scripts/validate-plugin-versions.sh` passes (dev-tools has plugin.json;
  agent-meta is unchanged vs `main`).
- `shellcheck` on the three scripts if available.
- Smoke-test each script against the real `claude` binary: `dump-strings.sh`
  produces a cache and is idempotent on re-run; `pull-fn.sh` retrieves a known
  anchor's body; `grep-context.sh` returns a window around a known UI string.
- Em-dash / dash-stand-in grep clean across SKILL.md and the reference file.
- Skill self-check: description triggers on "extract Claude Code's system
  prompt" and on general "inspect a CLI binary" asks; technique-first body reads
  correctly with Claude as one example.

## Out of scope

- Deleting the original pickletown skill (`plugin/skills/claude-binary-spelunking/`):
  a separate pt self-dev decision, tracked outside this PR.
- A general anchor-cataloging script (too binary-specific).
- Covering compiled Go/Rust/C beyond a short honest boundary note.
