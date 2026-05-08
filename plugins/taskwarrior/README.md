# taskwarrior

Token-dense recipes for the [taskwarrior](https://taskwarrior.org/) CLI.

## What it does

Provides a skill that activates when you query or modify tasks. Captures dense recipes for the operations that otherwise dump thousands of characters per call:

- **Listing:** `task <filter> dense` (named report) or `task <filter> export | jq -r '...'`
- **Single-field lookup:** `task <uuid> _get <field>` instead of `task <uuid> info`
- **Multi-task lookup:** `task uuid:A,B,C export | jq -r '...'` instead of `task A info && task B info && ...`
- **Full-text search:** `task export | jq -r '.[] | select(.annotations[]?.description | test("..."))'`
- **Description-length convention:** ≤ 100 chars; long context goes in annotations.

## Companion config

This skill assumes `~/.taskrc` has been configured with a named `dense` report. See the design doc at `docs/superpowers/specs/2026-05-08-taskwarrior-token-density-design.md` for the exact `.taskrc` block.

## Why

`task list` and `task <id> info` together account for ~80% of taskwarrior I/O cost in Claude sessions (~13K tokens/day baseline). The dense recipes cut listing cost ~5-8× and replace per-task `info` calls with single-field `_get` or batched `export`.
