# hk Plugin

Wires up what `hk agent hooks`, `hk agent instructions` and `hk agent mcp` print for Claude Code, so you don't have to paste it into every project. It targets hk 2.5 and later, where `hk agent stop-hook` exists.

Both hooks do nothing unless the project has an hk config (`hk.pkl`, `hk.local.pkl`, or either under `.config/`) at or above the working directory, and `hk` runs there and knows `agent stop-hook`. A mise shim with no version set doesn't count, and neither does hk older than 2.5 (where `agent stop-hook` is a usage error that exits 2, which Claude Code would treat as a block).

## Installation

```bash
/plugin install hk@pickled-claude-plugins
```

## Skills

### hk-creating-checks

How to write a check (step) in `hk.pkl` on the hk version the project actually runs: builtin vs custom step, command forms, declaring `read`/`write`/`destructive` effects so `--safe` accepts it, and what differs across 1.x, 1.55, and 2.x. Built from upstream docs and release notes (current as of hk 2.7.1); examples were run against hk 2.0.0.

## Hooks

- **SessionStart** injects the output of `hk agent instructions --target claude-code`, run at session start so it tracks the project's hk version.
- **Stop** runs `hk agent stop-hook --target claude-code --timeout 570`, which is exactly what `hk agent hooks --target claude-code` prints. hk does the work: it runs `hk run check --safe`, stands down when `stop_hook_active` is set, passes when there is no `check` hook, and prints `{"decision":"block",...}` when the check fails. The plugin's script only checks that hk is there to ask.

`--safe` refuses steps whose effect is unknown, so custom steps in `hk.pkl` need an `effect` (`read` or `write`) or Stop will block until they have one.

## MCP server

The plugin registers hk's MCP server, `plugin:hk:hk`, so the `hk agent instructions` text that tells Claude to ask the hk MCP server has something to talk to. It gives Claude persistent runs, cancellation, paged logs, diagnostics and diffs.

A plugin MCP server starts in every project where the plugin is enabled and can't be made conditional, and a command that fails shows up as a failed server. So the plugin starts `hooks/hk-mcp.sh`: in a project with an hk config and hk 2.5 or later it becomes `hk mcp --root <project>`, and anywhere else it answers the MCP handshake and advertises no tools. Disable it per project from `/mcp` if you don't want it.

## Relationship to dev-tools

The `dev-tools` plugin ships the `hk` skill (how to author and troubleshoot `hk.pkl`). This plugin only wires the agent hooks, so they can be disabled without losing the skill.
