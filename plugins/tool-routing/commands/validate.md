---
description: Validate tool-routing plugin installation and hooks format
---

# Validate Tool-Routing Plugin

Run these steps to verify the tool-routing plugin is correctly installed and working.

## Step 1: Validate Plugin Manifest

Run `claude plugin validate` on the plugin directory:

```bash
claude plugin validate /path/to/plugins/tool-routing
```

This checks that `.claude-plugin/plugin.json` exists and is valid JSON.

## Step 2: Run Plugin Structure Tests

The plugin includes pytest tests that validate hooks.json format:

```bash
cd /path/to/plugins/tool-routing
uv run pytest tests/test_plugin_structure.py -v
```

These tests catch **silent failures** where hooks.json is valid JSON but wrong format:

| Wrong Format | Correct Format |
|--------------|----------------|
| `"hooks": [...]` (array) | `"hooks": {"PreToolUse": [...]}` (object keyed by event) |
| `"matcher": {"tool_name": "X"}` | `"matcher": "X"` (string pattern) |
| `"type": "preToolUse"` | `"type": "command"` |
| `$CLAUDE_PLUGIN_ROOT` | `${CLAUDE_PLUGIN_ROOT}` (with braces) |

## Step 3: Run Route Tests

Test that route patterns match correctly:

```bash
uv run tool-routing test
```

This runs inline test fixtures defined in `hooks/tool-routes.yaml`.

## Step 4: Test at Runtime

After the above pass, test that hooks actually fire:

1. **Restart Claude Code** (hooks are captured at startup)
2. **Try a blocked tool call**, e.g.:
   ```
   WebFetch https://github.com/owner/repo/pull/123
   ```
3. **Expected**: Request blocked with message suggesting `gh pr view`

If the WebFetch goes through instead of being blocked, the hooks aren't loading. Check:
- Plugin is enabled: `/plugin` → Manage Plugins
- Restart happened after latest changes
- `claude --debug` for hook loading errors

## Step 5: Check Debug Output (if issues)

Run Claude Code with debug logging:

```bash
claude --debug
```

Look for:
- `[DEBUG] Executing hooks for PreToolUse:WebFetch`
- Any errors during hook registration

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| WebFetch not blocked | Hooks not loading | Check format, restart Claude Code |
| "No module named tool_routing" | Wrong working directory | Run from plugin root with `uv run` |
| Plugin not in list | Missing manifest | Create `.claude-plugin/plugin.json` |
| Tests fail on matcher format | Old hooks.json format | Update to object-keyed structure |

## Step 6: Run Integration Tests (Optional)

For full verification that hooks actually block at runtime, use subagents:

1. **Get test cases:**
   ```bash
   uv run tool-routing integration-test --list > .tmp/integration-tests.json
   ```

2. **Spawn a subagent** to execute the tests. The subagent should:
   - Attempt each tool call exactly as specified
   - Report results as JSON array: `[{"id": 0, "result": "blocked", "message": "..."}, ...]`

3. **Save the subagent's JSON report** to `.tmp/integration-report.json`

4. **Evaluate results:**
   ```bash
   uv run tool-routing integration-test --evaluate \
     --tests .tmp/integration-tests.json \
     --report .tmp/integration-report.json
   ```

This verifies the full integration path: Claude Code → hooks → tool-routing check → block/allow.

## Copying These Tests to Other Plugins

The `tests/test_plugin_structure.py` file can be adapted for any plugin with hooks. Copy it and adjust:
- `PLUGIN_ROOT` path
- Which tests to skip if plugin doesn't use certain features
