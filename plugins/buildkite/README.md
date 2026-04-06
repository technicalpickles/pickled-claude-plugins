# buildkite

Buildkite CI tools for Claude Code. Consolidates build investigation and pipeline development skills, and enforces tool preferences via a PreToolUse hook.

## What it does

- Skills for investigating Buildkite builds and developing pipelines
- Hook that intercepts Buildkite-related Bash commands and redirects to preferred tools (bktide, MCP) over the `bk` CLI

## Configuration

User config: `~/.config/pickled-claude-plugins/buildkite.yml`

Defaults: `config/defaults.yml` (copy and customize)

## Tool preference

The hook enforces a preferred tool order: `bktide` > MCP > `bk`. With `strict: true` (the default), non-preferred tools are blocked. Set `strict: false` to warn instead.
