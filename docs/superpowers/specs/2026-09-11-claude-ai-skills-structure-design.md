# claude.ai Skills Structure — Design

**Date:** 2026-09-11
**Status:** Draft, pending user approval
**Author:** brainstorm with Claude

## Problem

This repo hosts Claude Code plugins under `plugins/{name}/`, with everything — commit
scopes, `bump-version.sh`, the generated README plugin table, marketplace entries — built
around that convention. Separately, there's a need for **claude.ai Skills**: the chat
product's own skill format (Settings → Capabilities → Skills), uploaded as a zip, usable
in general chat with no filesystem/CLI/MCP access.

A first one, `vault-capture`, was built this session as a chat-only rewrite of the
`second-brain:capture` Claude Code skill. It went through two location guesses (dotfiles,
then a bare top-level `claude-ai-skills/` dir in this repo) before being parked: the
top-level dir didn't fit a repo whose every convention assumes `plugins/{name}/`, and
being a lone top-level artifact hid the fact that `vault-capture` is tightly coupled to
`second-brain`'s conventions (`note-format.md`, the vault's own `CLAUDE.md`) — a coupling
that was invisible from the directory structure.

During brainstorming it became clear this isn't a one-off: a second candidate
(`writing-tools`'s scannability/undisclosed-context skills) surfaced immediately, so this
needs to be a repeatable pattern across multiple source plugins, not a single ad hoc
export.

## Goals

1. Give claude.ai-skill ports a home that reflects their coupling to a specific source
   plugin, so the relationship isn't lost.
2. Make commits touching a port fit the repo's existing commit-scope convention
   (`feat(second-brain): ...`) without a carve-out.
3. Share build/packaging logic across ports instead of duplicating a `build.sh` per port.
4. Distinguish, in process (not just informally), between a **straight port** (source
   skill has no tool/CLI/MCP/filesystem dependency — closer to copy-paste) and an
   **adapted port** (source skill assumes capabilities claude.ai chat doesn't have, and
   needs an explicit capability-gap pass).
5. Migrate the existing `vault-capture` work into the new structure.

## Non-goals

- Not building the `writing-tools` port in this pass — it's the second, confirming
  example of the pattern, but its own port is future work.
- Not making claude.ai-skill ports real Claude Code plugins (no `plugin.json`, no
  marketplace entry, no `/plugin install`). They stay a separate, manually-uploaded
  product, per the original `vault-capture` scoping decision.
- Not retroactively applying full `superpowers:writing-skills` TDD rigor to
  `vault-capture` itself — that decision (lightweight pass) was made and executed before
  this structural rethink; the new rigor requirement applies going forward.

## Approach

### 1. Directory convention — colocated inside the source plugin

```
plugins/{plugin-name}/claude-ai-skills/{skill-name}/
  SKILL.md
  references/        # optional, same shape as Claude Code skills
```

Sibling to that plugin's `skills/`, `hooks/`, etc. Not a Claude Code plugin skill itself —
doesn't appear in `/plugin install`, has no `plugin.json` entry, isn't part of the
generated README table. The only reason it's nested here is organizational: it sits next
to the conventions it mirrors, and a commit touching it naturally scopes to that plugin
(`feat(second-brain): add vault-capture claude.ai skill`), satisfying the existing
commit-scope rule with no special-casing.

A plugin's `claude-ai-skills/` directory can hold more than one skill (a family), same as
`skills/` can.

### 2. Shared build tooling

One script, `scripts/build-claude-ai-skill.sh <plugin> <skill-name>`, replacing the
per-directory `build.sh` from the original design. It zips
`plugins/<plugin>/claude-ai-skills/<skill-name>/` into
`plugins/<plugin>/claude-ai-skills/dist/<skill-name>.zip`, with `SKILL.md` at the zip
root (the shape claude.ai's uploader expects). No per-plugin copies to keep in sync.

### 3. Docs — porting guide

Root `CLAUDE.md` gets a short pointer section, following the existing pattern used for
`docs/versioning.md`, linking to a new `docs/claude-ai-skill-porting.md`. That doc covers:

- The directory/build convention from sections 1-2 above.
- **A porting checklist**, applied when adapting a Claude Code skill into a claude.ai
  skill:
  - Does the source skill invoke tools, a CLI, MCP, or the filesystem?
    - **No** → straight port. The instructions carry over close to as-is; review is
      lightweight.
    - **Yes** → adapted port. Do a capability-gap pass: enumerate what's lost without
      filesystem/CLI/MCP access, decide per capability whether to disclose the gap
      plainly or find a chat-safe equivalent (never fake it), and check whether any
      reference data needs to be baked into `references/` because it previously lived
      only in an external config the source skill could read live (as `jd-map.md` had to
      be, standing in for the vault's own `CLAUDE.md`).
  - Either way, the port goes through the full `superpowers:writing-skills` TDD process
    (baseline subagent runs, rationalization tables) before being considered done — the
    checklist changes *what* gets adapted, not whether it gets tested.

### 4. Migration

- Move `claude-ai-skills/vault-capture/` (currently untracked, top-level) to
  `plugins/second-brain/claude-ai-skills/vault-capture/`.
- Drop the top-level `claude-ai-skills/README.md` and `claude-ai-skills/build.sh` —
  superseded by `docs/claude-ai-skill-porting.md` and the shared script.
- Rebuild `dist/vault-capture.zip` via the new shared script at its new location.

## Testing / Verification

- `scripts/build-claude-ai-skill.sh second-brain vault-capture` produces a zip with
  `SKILL.md` at its root and the expected `references/jd-map.md` alongside it.
- `git status` shows the migrated files as untracked in their new location, and the old
  top-level `claude-ai-skills/` dir is gone.
- Root `CLAUDE.md` and `docs/claude-ai-skill-porting.md` cross-reference each other, same
  as the existing `docs/versioning.md` link.
