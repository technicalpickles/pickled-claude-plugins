---
description: Validate tool-routing plugin installation and hooks format
---

# Validate Tool-Routing Plugin

Run these steps to verify the tool-routing plugin is correctly installed and working.

## Monorepo Context

This plugin is part of the `pickled-claude-plugins` monorepo. Routes are contributed by multiple plugins:

| Plugin | Route Location | Routes |
|--------|----------------|--------|
| tool-routing | `hooks/tool-routes.yaml` | bash-cat-heredoc, bash-echo-*, tool-routing-manual-test |
| dev-tools | `hooks/tool-routes.yaml` | atlassian |
| git | `skills/pull-request/tool-routes.yaml` | github-pr, git-commit-multiline, gh-pr-create-multiline |
| ci-cd-tools | `skills/working-with-buildkite-builds/tool-routes.yaml` | buildkite |
| mcpproxy | `skills/working-with-mcp/tool-routes.yaml` | bash-mcp-cli, bash-mcp-tool |

## Step 1: Validate Plugin Manifests

Run `claude plugin validate` on each plugin with a manifest:

```bash
# From repo root
for plugin in plugins/*/; do
  if [ -d "$plugin/.claude-plugin" ]; then
    echo "=== Validating $plugin ==="
    claude plugin validate "$plugin"
  fi
done
```

## Step 2: Run Plugin Structure Tests

The plugin includes pytest tests that validate hooks.json format:

```bash
cd plugins/tool-routing
uv run pytest tests/test_plugin_structure.py -v
```

These tests catch **silent failures** where hooks.json is valid JSON but wrong format:

| Wrong Format | Correct Format |
|--------------|----------------|
| `"hooks": [...]` (array) | `"hooks": {"PreToolUse": [...]}` (object keyed by event) |
| `"matcher": {"tool_name": "X"}` | `"matcher": "X"` (string pattern) |
| `"type": "preToolUse"` | `"type": "command"` |
| `$CLAUDE_PLUGIN_ROOT` | `${CLAUDE_PLUGIN_ROOT}` (with braces) |

## Step 3: Run Route Tests (All Plugins)

Test that route patterns match correctly across **all enabled plugins**:

```bash
# From repo root
CLAUDE_PROJECT_ROOT="$PWD" uv run --directory plugins/tool-routing tool-routing test
```

This uses manifest-driven discovery via `claude plugin list --json` to find routes from all enabled plugins with `routes.json` manifests.

**Expected output:** Routes from enabled plugins with route manifests, all tests passing.

**Note:** The number of sources depends on which plugins are enabled and have `routes.json` manifests. Use `tool-routing list` to see exactly which sources are discovered.

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
| Fewer sources than expected | Plugin not enabled, or wrong project path | See Step 5a and route-discovery.md |

## Step 5a: Verify Cross-Plugin Route Discovery

**Critical check:** Ensure routes from enabled plugins are discovered.

```bash
# From repo root
CLAUDE_PROJECT_ROOT="$PWD" uv run --directory plugins/tool-routing tool-routing list
```

**Expected:** "Routes (merged from N sources)" where N matches enabled plugins with route manifests.

If you see fewer sources than expected:

1. **Check plugin is enabled:**
   ```bash
   claude plugin list --json | jq '.[] | select(.id | contains("tool-routing")) | {id, enabled, scope, projectPath}'
   ```

2. **Check project path matches:** Local-scoped plugins use **exact path matching**. If you're running from `plugins/tool-routing/` but the plugin is scoped to the repo root, it won't be discovered. Set `CLAUDE_PROJECT_ROOT` to match the plugin's `projectPath`.

3. **Check routes.json exists:**
   ```bash
   cat ~/.claude/plugins/cache/{marketplace}/{plugin}/{version}/.claude-plugin/routes.json
   ```

4. See `docs/route-discovery.md#troubleshooting` for more diagnostics

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
