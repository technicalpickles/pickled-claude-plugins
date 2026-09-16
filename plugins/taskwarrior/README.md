# taskwarrior

Token-dense recipes for the [taskwarrior](https://taskwarrior.org/) CLI.

## What it does

Provides a skill that activates when you query or modify tasks. Captures dense recipes for the operations that otherwise dump thousands of characters per call:

- **Listing:** `task <filter> dense` (named report) or `task <filter> export | jq -r '...'`
- **Single-field lookup:** `task _get <uuid>.<field>` instead of `task <uuid> info`
- **Multi-task lookup:** `task A B C export | jq -r '...'` (space-separated UUIDs) instead of `task A info && task B info && ...`
- **Full-text search:** `task export | jq -r '.[] | select(.annotations[]?.description | test("..."))'`
- **Description-length convention:** ≤ 100 chars; long context goes in annotations.

## Hooks

- A `PreToolUse:Write|Edit` hook nudges taskwarrior UUID-safety whenever the content being written cites a bare integer task reference (`task 518`, `taskwarrior 518`, `task #518`). Fires on any Write or Edit, not just durable-looking paths -- an earlier, path-scoped version of this check (once part of personal dotfiles config, restricted to `.parkinglot/`, `.beans/`, and the auto-memory dir) missed a real incident where a bare ID landed in `CLAUDE.md` and `docs/setup-notes.md`. See `hooks/nudge-durable-write-bare-id.py`.
- A `PreToolUse:Bash` hook guards two risky patterns in one pass: mutating a task (`done`/`annotate`/`modify`/`depends`/`delete`/`start`/`stop`) by its plain numeric ID, and a `git commit` whose message cites a bare integer ID. See `hooks/guard-bash-task-citation.py`.
- A `PostToolUse:Bash` hook resolves the UUID of a task just created with `task add`, without needing a follow-up tool call. It detects a `Created task <N>.` message, resolves `N` to its UUID via `task _get <N>.uuid`, and injects both into context. This exists because in practice the follow-up UUID resolution almost never happens on its own (measured: 32 of 33 `task add` calls across a week of sessions had no inline resolution) -- the bare integer is what's sitting in context when a durable artifact gets written later, so removing the need to remember the follow-up removes the leak at its source. See `hooks/resolve-added-task-uuid.py`.

## Companion config

This skill assumes `~/.taskrc` has been configured with a named `dense` report. See the design doc at `docs/superpowers/specs/2026-05-08-taskwarrior-token-density-design.md` for the exact `.taskrc` block.

## Why

`task list` and `task <id> info` together account for ~80% of taskwarrior I/O cost in Claude sessions (~13K tokens/day baseline). The dense recipes cut listing cost ~5-8× and replace per-task `info` calls with single-field `_get` or batched `export`.
