# hk Plugin

Brings [hk](https://hk.jdx.dev)'s coding-agent integration to Claude Code, in projects that use hk. hk is a git hook manager: a project's `hk.pkl` (written in the Pkl config language) defines *steps*, which are lint and format commands, and hk runs them as git hooks or on demand with `hk check` and `hk fix`.

hk can print what an agent needs: a Stop hook (`hk agent hooks`), a block of instructions (`hk agent instructions`), and an MCP server (`hk mcp`). Normally you copy those into each project's Claude Code settings. This plugin does it once, for every project:

- **SessionStart** injects hk's instructions.
- **Stop** runs the project's `check` hook (what `hk check` runs) before Claude finishes, and blocks if it fails.
- **MCP** registers hk's MCP server.

## Installation

```bash
/plugin install hk@pickled-claude-plugins
```

Requires hk 2.6 or later in the project, and `jq` on PATH.

## When it's active

All three pieces stay off unless every one of these holds, and they do nothing and print nothing otherwise:

- An hk config file exists at or above the directory Claude is working in: `hk.pkl`, `hk.local.pkl`, or either under `.config/`. This is the same upward walk hk does, and it checks only that the file exists, so a broken `hk.pkl` still counts.
- `hk` runs there. A mise shim with no hk version set fails this, as does `hk` missing from PATH.
- hk is 2.6 or later, read from `hk --version`. hk 2.5 added `agent stop-hook` and 2.6 made it pass quietly in a project whose config has no `check` hook (2.5.x blocks there). Older hk answers `agent stop-hook` with a usage error that exits 2, which Claude Code would treat as a block.

The same check gates all three pieces, even though `hk agent instructions` and `hk mcp` exist from 1.55, because the plugin is built around the Stop hook and a project on an older hk would otherwise get half of it. The check runs `hk --version` once per SessionStart, Stop and MCP launch.

## Hooks

Both hooks take the directory from the hook payload's `cwd` and run hk there.

- **SessionStart** injects the output of `hk agent instructions --target claude-code` as context. It fires on startup, resume, clear and compact (the hook has no matcher), so the instructions come back after a `/clear`. If hk fails to print them, it stays silent.
- **Stop** runs `hk agent stop-hook --target claude-code --timeout 570`, which is what `hk agent hooks --target claude-code` prints. hk does the work. It runs `hk run check --safe`, passes when `stop_hook_active` is set (Claude Code's flag for "already continuing because of a Stop hook", so a check Claude can't fix doesn't trap it in a loop), and prints `{"decision":"block","reason":...}` when the check fails. By hk's docs it always exits 0. `--timeout` is in seconds: hk stops the check at 570 and reports a block, and `hooks.json` gives Claude Code's side 600. The script relays hk's output and exit status unchanged.

`--safe` refuses steps whose effect is unknown, so custom steps in `hk.pkl` need an `effect` (`read` or `write`) or Stop will block until they have one. See the `hk-creating-checks` skill.

## MCP server

The plugin declares hk's MCP server in `plugin.json` (named `hk`, which Claude Code shows as `plugin:hk:hk`), so the instructions' advice to ask the hk MCP server has something behind it. It gives Claude persistent runs, cancellation, paged logs, diagnostics and diffs.

A plugin MCP server starts in every project where the plugin is enabled and can't be made conditional, and a command that fails shows up as a failed server. So the plugin starts `hooks/hk-mcp.sh`, which passes `${CLAUDE_PROJECT_DIR}` as the project root. In a project that passes the checks above it becomes `hk mcp --root <project>`. Anywhere else it serves an inert session: it answers the MCP handshake and `ping` (as server `hk`, version `inactive`), advertises no tools, and ignores everything else. Disable the server per project from `/mcp` if you don't want it.

## Skills

### hk-creating-checks

How to write a check (a step) in `hk.pkl` on the hk version the project actually runs: builtin versus custom step, command forms, declaring `read`, `write` or `destructive` effects so `--safe` accepts it, and what differs across hk before 1.55, 1.55 and later, and 2.x. Built from upstream docs and release notes (current as of hk 2.7.1); the 2.x examples were run against hk 2.0.0 and 2.7.1, and the 1.x forms are marked unverified.

## Relationship to dev-tools

The `dev-tools` plugin ships the `hk` skill (installing hk, hook basics, the builtin list). This plugin ships the agent integration and the skill for writing steps, so the hooks can be disabled without losing the general skill.
