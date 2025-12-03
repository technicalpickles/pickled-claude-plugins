# CLI Reference

The tool-routing plugin provides a command-line interface for checking tool calls, running tests, and listing routes.

## Installation

The CLI is invoked via `uv run`:

```bash
cd plugins/tool-routing
uv run tool-routing <command>
```

## Commands

### check

Check a tool call against all routes. This is the hook entry point.

```bash
uv run tool-routing check
```

**Input:** Reads a JSON tool call from stdin:

```json
{
  "tool_name": "WebFetch",
  "tool_input": {
    "url": "https://github.com/foo/bar/pull/123"
  }
}
```

**Output:**
- Exit code `0`: Tool call allowed
- Exit code `2`: Tool call blocked (message printed to stderr)

**Example - Allowed:**

```bash
echo '{"tool_name": "WebFetch", "tool_input": {"url": "https://example.com"}}' | \
  uv run tool-routing check
echo $?  # 0
```

**Example - Blocked:**

```bash
echo '{"tool_name": "WebFetch", "tool_input": {"url": "https://github.com/foo/bar/pull/123"}}' | \
  uv run tool-routing check
# stderr: Use `gh pr view <number>` for GitHub PRs...
echo $?  # 2
```

**With debug output:**

```bash
TOOL_ROUTING_DEBUG=1 uv run tool-routing check
```

Debug output shows:
```
❌ Tool Routing: github-pr
Matched: https://github.com/foo/bar/pull/123
Pattern: github\.com/[^/]+/[^/]+/pull/\d+

Use `gh pr view <number>` for GitHub PRs.
...
```

### test

Run all inline test fixtures from all route sources.

```bash
uv run tool-routing test
```

**Output:** Shows pass/fail for each test, grouped by source file:

```
/path/to/plugins/tool-routing/hooks/tool-routes.yaml
  ✓ github-pr: PR URL should block
  ✓ github-pr: repo URL should allow
  ✓ github-pr: issues URL should allow
  ✓ atlassian: Jira URL should block
  ✓ atlassian: Confluence URL should block

/path/to/project/.claude/tool-routes.yaml
  ✓ project-route: internal URL should block

15 passed, 0 failed
```

**On failure:**

```
/path/to/hooks/tool-routes.yaml
  ✗ github-pr: PR URL should block
      Expected: block, Got: allow

14 passed, 1 failed
```

**Contains check failure:**

```
  ✗ github-pr: should suggest gh CLI
      Expected message to contain 'gh pr view'
```

**Exit codes:**
- `0`: All tests passed
- `1`: One or more tests failed, or configuration error

### list

Show all merged routes from all sources.

```bash
uv run tool-routing list
```

**Output:**

```
Routes (merged from 2 sources):

github-pr (from: /path/to/plugins/tool-routing/hooks/tool-routes.yaml)
  tool: WebFetch
  pattern: github\.com/[^/]+/[^/]+/pull/\d+
  tests: 3

atlassian (from: /path/to/plugins/tool-routing/hooks/tool-routes.yaml)
  tool: WebFetch
  pattern: https?://[^/]*\.atlassian\.net
  tests: 2

bash-mcp-cli (from: /path/to/plugins/tool-routing/hooks/tool-routes.yaml)
  tool: Bash
  pattern: ^\s*mcp\s+
  tests: 2
```

**Exit codes:**
- `0`: Routes listed successfully
- `1`: Configuration error (e.g., route conflict)

## Exit Code Summary

| Command | Code | Meaning |
|---------|------|---------|
| `check` | 0 | Tool call allowed |
| `check` | 2 | Tool call blocked |
| `test` | 0 | All tests passed |
| `test` | 1 | Tests failed or config error |
| `list` | 0 | Success |
| `list` | 1 | Config error |

The `check` command uses exit code `2` (not `1`) for blocked calls because Claude Code hooks interpret exit code `2` as "block the tool call."

## Environment Variables

| Variable | Used By | Description |
|----------|---------|-------------|
| `CLAUDE_PLUGIN_ROOT` | All commands | This plugin's directory |
| `CLAUDE_PLUGINS_DIR` | All commands | Directory containing all plugins |
| `CLAUDE_PROJECT_ROOT` | All commands | Project root for local routes |
| `TOOL_ROUTING_DEBUG` | `check` | Enable debug output (`1`, `true`, or `yes`) |

Claude Code sets the `CLAUDE_*` variables automatically when invoking hooks.

## Hook Integration

The plugin registers as a `preToolUse` hook in `hooks/hooks.json`:

```json
{
  "hooks": [
    {
      "matcher": { "tool_name": "WebFetch" },
      "hooks": [{
        "type": "preToolUse",
        "command": "uv run --project $CLAUDE_PLUGIN_ROOT tool-routing check"
      }]
    },
    {
      "matcher": { "tool_name": "Bash" },
      "hooks": [{
        "type": "preToolUse",
        "command": "uv run --project $CLAUDE_PLUGIN_ROOT tool-routing check"
      }]
    }
  ]
}
```

**Hook flow:**

1. Claude Code detects a `WebFetch` or `Bash` tool call
2. Triggers the `preToolUse` hook
3. Passes tool call JSON to `tool-routing check` via stdin
4. If exit code is `2`, Claude Code blocks the call and shows the stderr message
5. If exit code is `0`, Claude Code proceeds with the tool call

## Scripting Examples

**Test a single fixture:**

```bash
echo '{"tool_name": "Bash", "tool_input": {"command": "mcp list-tools"}}' | \
  uv run tool-routing check
```

**Check if a pattern would block:**

```bash
if echo '{"tool_name": "WebFetch", "tool_input": {"url": "https://github.com/foo/bar/pull/1"}}' | \
   uv run tool-routing check 2>/dev/null; then
  echo "Allowed"
else
  echo "Blocked"
fi
```

**Run tests in CI:**

```bash
cd plugins/tool-routing
uv run tool-routing test || exit 1
```

**List routes as part of validation:**

```bash
uv run tool-routing list > /dev/null || echo "Config error!"
```
