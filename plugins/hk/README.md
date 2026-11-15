# hk Plugin

Brings [hk](https://hk.jdx.dev)'s coding-agent integration to Claude Code, in projects that use hk. hk is a git hook manager: a project's `hk.pkl` (written in the Pkl config language) defines *steps*, which are lint and format commands, and hk runs them as git hooks or on demand with `hk check` and `hk fix`.

hk can print what an agent needs: a Stop hook (`hk agent hooks`) and a block of instructions (`hk agent instructions`). Normally you copy those into each project's Claude Code settings. This plugin does it once, for every project, and follows you into an hk repo even when the session started somewhere else, such as a parent directory full of clones:

- **PostToolUse** injects hk's instructions the first time a tool call runs inside an hk project.
- **Stop** runs the project's `check` hook (what `hk check` runs) before Claude finishes, and blocks if it fails.

## Installation

```bash
/plugin install hk@pickled-claude-plugins
```

Requires hk 2.6 or later in the project, and `jq` on PATH.

## When it's active

Both pieces stay off unless every one of these holds, and they do nothing and print nothing otherwise:

- An hk config file exists at or above the directory Claude is working in: `hk.pkl`, `hk.local.pkl`, or either under `.config/`. This is the same upward walk hk does, and it checks only that the file exists, so a broken `hk.pkl` still counts.
- `hk` runs there. A mise shim with no hk version set fails this, as does `hk` missing from PATH.
- hk is 2.6 or later, read from `hk --version`. hk 2.5 added `agent stop-hook` and 2.6 made it pass quietly in a project whose config has no `check` hook (2.5.x blocks there). Older hk answers `agent stop-hook` with a usage error that exits 2, which Claude Code would treat as a block.

The same check gates both pieces, even though `hk agent instructions` exists from 1.55, because the plugin is built around the Stop hook and a project on an older hk would otherwise get half of it. The config walk runs first, so a tool call outside any hk project never starts hk. `hk --version` runs once per Stop, and on each PostToolUse call until the instructions have been injected.

## Hooks

Both hooks take the directory from the hook payload's `cwd` and run hk there. Claude Code sets `cwd` on every tool call and follows a Bash `cd`, so neither hook cares where the session started.

- **PostToolUse** (on `Bash`, `Read`, `Edit`, `MultiEdit` and `Write`) injects the output of `hk agent instructions --target claude-code` as context, once per session. A marker file named for the session id in `${TMPDIR:-/tmp}` records that it happened. Calls outside an hk project do nothing and leave no marker, so a session that starts in a parent directory gets the instructions on the first tool call after it moves into a repo. The instructions do not come back after `/compact`. If hk fails to print them, it stays silent and tries again on the next call.
- **Stop** runs `hk agent stop-hook --target claude-code --timeout 570`, which is what `hk agent hooks --target claude-code` prints. hk does the work. It runs `hk run check --safe`, passes when `stop_hook_active` is set (Claude Code's flag for "already continuing because of a Stop hook", so a check Claude can't fix doesn't trap it in a loop), and prints `{"decision":"block","reason":...}` when the check fails. By hk's docs it always exits 0. `--timeout` is in seconds: hk stops the check at 570 and reports a block, and `hooks.json` gives Claude Code's side 600. The script relays hk's output and exit status unchanged.

`--safe` refuses steps whose effect is unknown, so custom steps in `hk.pkl` need an `effect` (`read` or `write`) or Stop will block until they have one. See the `hk-creating-checks` skill.

## No MCP server

Earlier versions registered `hk mcp` as an MCP server. Claude Code starts a plugin's MCP servers once, in the directory the session started in, so the server could never follow a `cd` into an hk repo, and from a parent directory it sat inert. hk's instructions say to ask the MCP server first but also give the CLI fallback (`hk run check --format jsonl --safe`), which works from Bash in any repo. To get the MCP server back in one project, add `hk mcp` to that project's `.mcp.json`.

## Skills

### hk-creating-checks

How to write a check (a step) in `hk.pkl` on the hk version the project actually runs: builtin versus custom step, command forms, declaring `read`, `write` or `destructive` effects so `--safe` accepts it, and what differs across hk before 1.55, 1.55 and later, and 2.x. Built from upstream docs and release notes (current as of hk 2.7.1); the 2.x examples were run against hk 2.0.0 and 2.7.1, and the 1.x forms are marked unverified.

## Relationship to dev-tools

The `dev-tools` plugin ships the `hk` skill (installing hk, hook basics, the builtin list). This plugin ships the agent integration and the skill for writing steps, so the hooks can be disabled without losing the general skill.
