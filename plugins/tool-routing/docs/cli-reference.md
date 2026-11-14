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

**Output:** Always exits `0`, so a broken route or bad input never blocks a
call (fail open).

- Allowed: prints nothing.
- Blocked: prints a PreToolUse decision to stdout. Claude Code denies the call
  and shows the route's message to Claude.

**Example - Blocked:**

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Use `gh pr view <number>` for GitHub PRs.\n..."
  }
}
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

### overlap

Find routes that match the same command.

```bash
uv run tool-routing overlap --plugins-dir ../ --corpus tests/overlap-corpus.yaml
```

Replays every route's test inputs, and every case in the corpus file, against
all loaded routes. An `allow` input matched by any route is an error. A
`block` input also matched by another route is a warning. A corpus case whose
matching routes differ from its `routes` list is an error. Exits 1 on errors.

`--plugins-dir` loads routes from each plugin's `routes.json` under that
directory, so the result covers exactly the plugins in a checkout and does not
depend on what is installed. `tool-routing test` takes the same flag. The
corpus in `tests/overlap-corpus.yaml` holds commands that mention a tool
without invoking it, where substring matching tends to misfire.

### test

Run all inline test fixtures from all route sources.

```bash
uv run tool-routing test
uv run tool-routing test --merged
```

Each route's tests run against that route alone, so a test asserts what its
own route does and routes from other plugins cannot fail or satisfy it. Pass
`--merged` to run every test against the whole merged table instead. That
finds routes that overlap on the same command.

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
| `check` | 0 | Always, blocked or not (a block is the JSON on stdout) |
| `test` | 0 | All tests passed |
| `test` | 1 | Tests failed or config error |
| `list` | 0 | Success |
| `list` | 1 | Config error |

`check` blocks through the JSON `permissionDecision` rather than exit code `2`.
Exit `2` also blocks, but sends stderr as plain feedback; the JSON form is the
structured PreToolUse decision, and keeps every other outcome at exit `0`.

## Environment Variables

| Variable | Used By | Description |
|----------|---------|-------------|
| `CLAUDE_PLUGIN_ROOT` | All commands | This plugin's directory |
| `CLAUDE_PLUGINS_DIR` | All commands | Directory containing all plugins |
| `CLAUDE_PROJECT_ROOT` | All commands | Project root for local routes |
| `TOOL_ROUTING_DEBUG` | `check` | Enable debug output (`1`, `true`, or `yes`) |

Claude Code sets the `CLAUDE_*` variables automatically when invoking hooks.

## Hook Integration

The plugin registers a `PreToolUse` hook in `hooks/hooks.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "WebFetch|Bash",
        "hooks": [
          {
            "type": "command",
            "command": "uv run --quiet --directory \"${CLAUDE_PLUGIN_ROOT}\" tool-routing check"
          }
        ]
      }
    ]
  }
}
```

**Hook flow:**

1. Claude Code is about to run a `WebFetch` or `Bash` call
2. It runs `tool-routing check` with the tool call JSON on stdin
3. If a route matches, `check` prints a `permissionDecision: "deny"` decision,
   and Claude Code blocks the call and shows Claude the route's message
4. Otherwise `check` prints nothing, and the call goes through

## Scripting Examples

**Check if a call would block:** add it as a route test and run
`uv run tool-routing test`. `check` prints the deny decision on stdout when it
blocks and nothing when it allows.

**Run tests in CI:**

```bash
cd plugins/tool-routing
uv run tool-routing test || exit 1
```

**List routes as part of validation:**

```bash
uv run tool-routing list > /dev/null || echo "Config error!"
```
