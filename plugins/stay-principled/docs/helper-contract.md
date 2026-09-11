# `skill-advice` helper contract

`scripts/skill-advice.py` is a generic conditional-advice emitter for Claude Code PreToolUse hooks targeting the `Skill` tool. Nothing in it is plugin-specific; other plugins can wire it into their own hooks.

## Invocation

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/skill-advice.py" \
  --skill <name> \
  [--if-file <path>] \
  --advice <text>
```

## Behavior

| Condition | Result |
|---|---|
| stdin unparseable or empty | exit 0, no output |
| `tool_name` != `Skill` | exit 0, no output |
| `tool_input.skill` != `--skill` value | exit 0, no output |
| `--if-file` given and file does not exist | exit 0, no output |
| All checks pass | emit `hookSpecificOutput` JSON, exit 0 |
| Required args missing (`--skill`, `--advice`) | exit non-zero (argparse), error to stderr |

The non-zero exit on missing args is intentional. Settings.json misconfigurations should surface during development, not fail silently in production.

## Path resolution for `--if-file`

- Absolute path: used as-is.
- Relative path: resolved against `cwd` from the stdin payload, or `os.getcwd()` as fallback.

This means a single user-level hook in `~/.claude/settings.json` with `--if-file docs/agents/principles.md` will fire only in projects that have that file at their root, regardless of which project is active.

## Output shape

When all conditions match, stdout is exactly:

```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "<--advice text>"}}
```

Per Claude Code's hook documentation, `additionalContext` from PreToolUse hooks is injected as system-reminder-style context for the model's next turn. It does not block the call (`permissionDecision: "deny"` would do that). The model sees the advice and can act on it; the original Skill call still proceeds.

See the [Claude Code hooks reference](https://code.claude.com/docs/en/hooks.md) for the full schema.

## Reusability

To use this helper from another plugin, invoke it with a path that resolves to this plugin's cache directory:

```bash
python3 "$HOME/.claude/plugins/cache/pickled-claude-plugins/stay-principled/0.1.0/scripts/skill-advice.py" ...
```

Note: replace `0.1.0` with your installed version. The marketplace cache uses versioned paths; there is no `latest` symlink today.

The contract is stable. Future versions will not change argument names or output shape without a major version bump.
