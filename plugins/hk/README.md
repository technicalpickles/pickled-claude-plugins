# hk Plugin

Wires up what `hk agent hooks` and `hk agent instructions` print for Claude Code, so you don't have to paste it into every project. Both hooks do nothing unless there is an `hk.pkl` at or above the working directory and `hk` actually runs there (a mise shim with no version set doesn't count).

## Installation

```bash
/plugin install hk@pickled-claude-plugins
```

## Hooks

- **SessionStart** injects the output of `hk agent instructions --target claude-code`, run at session start so it tracks the project's hk version.
- **Stop** runs `hk run check --safe --format json`. A failing check blocks Stop (exit 2) and hands hk's output back to Claude; hk 2.0.0 exits 1 on failure, which Claude Code would treat as non-blocking. It stands down when `stop_hook_active` is set so an unfixable failure can't loop, and passes when `hk.pkl` has no `check` hook.

`--safe` refuses steps whose effect is unknown, so custom steps in `hk.pkl` need an `effect` (`read` or `write`) or Stop will block until they have one.

## Relationship to dev-tools

The `dev-tools` plugin ships the `hk` skill (how to author and troubleshoot `hk.pkl`). This plugin only wires the agent hooks, so they can be disabled without losing the skill.
