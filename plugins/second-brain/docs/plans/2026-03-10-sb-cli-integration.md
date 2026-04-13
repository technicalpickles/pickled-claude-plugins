# sb CLI Integration into Second-Brain Plugin

Bean: gt-szcn
Parent epic: gt-meu3 (Batch 5)
Date: 2026-03-10

## Goal

Refactor second-brain plugin commands to delegate data operations to the sb CLI (`@techpickles/sb`) instead of raw Bash/Read/Write calls. Reduces tool call count, improves reliability, and centralizes vault logic in a tested CLI.

## Architecture Decisions

### sb handles data, Claude handles decisions

sb does structured operations: note creation, moving, vault discovery, config, provenance. Claude keeps native Read/Write/Edit for prose editing, reading vault files for decision-making, and all routing/selection logic.

### Invocation via npx

All commands call sb as `npx @techpickles/sb <command>`. A shared reference file (`references/sb-cli.md`) defines the invocation pattern. Swapping to global install or a different package name later is a one-file change.

### Symlinks stay (for now)

`~/.claude/vaults/{name}` symlinks remain for `allowed-tools` permissions in command frontmatter. sb handles the actual vault operations. Symlinks can be removed when Claude Code supports dynamic permissions or sb handles all file access.

### allowed-tools changes

For commands that adopt sb:
- Remove: `Bash(date:*)`, `Bash(git rev-parse:*)`, `Bash(git branch:*)`, `Bash(mv:*)`
- Add: `Bash(npx @techpickles/sb:*)`
- Keep: `Read`/`Write`/`Edit` on vault symlink paths (for prose editing, reading notes)
- Keep: `Bash(ls:*)` only where still needed

## New File

### `skills/obsidian/references/sb-cli.md`

Single source of truth for sb invocation pattern and available commands. All commands that call sb load this reference. Contains prerequisite check, invocation prefix, and command quick-reference.

## Command Changes

### `insight` (heavy rewrite)

Before: 8+ tool calls (Read config, Bash git x3, Bash date, Write note, Bash ls for structure, Bash mv, Edit daily note)

After:
1. `sb note create --source auto --title "..." --content "..."` (provenance + date + filename + write)
2. `sb note context --note "..."` (structure discovery + keyword extraction)
3. Claude reads vault CLAUDE.md, makes routing decision
4. `sb note move --from "..." --to "..."` (routing execution)
5. `sb daily append --section "Links" --content "..."` (daily linking)

Still uses Claude native tools for: vault CLAUDE.md disambiguation rules, AskUserQuestion for routing, writing insight prose.

### `distill-conversation` (heavy rewrite)

Same sb calls as insight, batched. Conversation review and insight identification (pure Claude reasoning) unchanged. Batch routing uses `sb vault structure` once, then `sb note context` + `sb note move` per note. Batch daily linking uses `sb daily append` once with all links.

### `route` (heavy rewrite)

Before: Bash ls for structure, Read notes for analysis, Bash mv
After: `sb inbox list` to enumerate, `sb note context` per note, `sb vault structure` for destinations, `sb note move` to execute. Claude still makes routing decisions with disambiguation rules.

### `setup` (heavy rewrite)

Before: Manual config writing, symlink creation, .obsidian parsing
After: `sb init --name "..." --path "..."` for config writing. `sb permissions` for permission entries. Symlink creation stays. sb does .obsidian parsing, setup reads results for confirmation display.

### `search` (light touch)

Replace manual config parsing for collection name with `sb config qmd-collection`. qmd calls unchanged.

### `process-daily` (light touch)

Replace `date` + manual path construction with `sb daily path`. Prose cleaning, restructuring (bulk of command) unchanged.

### `link-project` (no change)

Deferred. Rarely used, symlinks staying anyway.

## Verification

1. Valid YAML frontmatter with updated `allowed-tools` on all changed commands
2. All sb-calling commands reference `references/sb-cli.md`
3. No orphaned raw Bash calls for operations sb now handles
4. Smoke test: reinstall plugin, run `/second-brain:insight` end-to-end with real vault
