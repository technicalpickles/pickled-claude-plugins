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

- A `PreToolUse:Write|Edit` hook nudges taskwarrior UUID-safety whenever you're about to write a file, regardless of which skill triggered it. It injects a reminder to verify any cited taskwarrior ID resolves to a UUID first, and never cite bare integer task IDs. See `hooks/nudge-durable-write-bare-id.py`.
- A `PreToolUse:Bash` hook guards against risky Bash commands that cite bare taskwarrior integer IDs. It detects patterns like `task 123 delete` in the command being run and injects a nudge to use the UUID instead. See `hooks/guard-bash-task-citation.py`.
- A `PostToolUse:Bash` hook resolves the UUID of a task just created with `task add`, without needing a follow-up tool call. It detects a `Created task <N>.` message, resolves `N` to its UUID via `task _get <N>.uuid`, and injects both into context. This exists because in practice the follow-up UUID resolution almost never happens on its own (measured: 32 of 33 `task add` calls across a week of sessions had no inline resolution) -- the bare integer is what's sitting in context when a durable artifact gets written later, so removing the need to remember the follow-up removes the leak at its source. See `hooks/resolve-added-task-uuid.py`.

## Companion config

This skill assumes `~/.taskrc` has been configured with a named `dense` report. See the design doc at `docs/superpowers/specs/2026-05-08-taskwarrior-token-density-design.md` for the exact `.taskrc` block.

## Why

`task list` and `task <id> info` together account for ~80% of taskwarrior I/O cost in Claude sessions (~13K tokens/day baseline). The dense recipes cut listing cost ~5-8× and replace per-task `info` calls with single-field `_get` or batched `export`.
