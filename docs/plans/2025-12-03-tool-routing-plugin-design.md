# Tool Routing Plugin Design

## Overview

Extract tool routing from `dev-tools` into a standalone plugin that intercepts tool calls and suggests better alternatives. The plugin supports configuration from multiple sources and allows other plugins to contribute routes.

## Motivation

1. **Explicit opt-in** - Tool routing should be a conscious choice, not bundled with unrelated skills
2. **Project-specific config** - Different projects need different routing rules
3. **Plugin-contributed routes** - Other plugins can register routes relevant to their domain (e.g., `ci-cd-tools` adds Buildkite routes)

## Architecture

### Configuration Sources

Routes are merged from multiple sources in order:

1. **Plugin-contributed routes** - Any plugin can include `hooks/tool-routes.yaml`
2. **Project-local routes** - `.claude/tool-routes.yaml` in the project root

Later sources can add routes but cannot override earlier ones. Duplicate patterns cause an error (fail loudly during development).

### Route Structure

```yaml
routes:
  # Route name (unique identifier)
  github-pr:
    # Which tool this route applies to
    tool: WebFetch

    # Regex pattern to match against tool input
    # WebFetch matches against url, Bash matches against command
    pattern: "github\\.com/[^/]+/[^/]+/pull/\\d+"

    # Message shown when route blocks a tool call
    message: |
      Use `gh pr view <number>` for GitHub PRs.

      This works for both public and private PRs and
      provides better formatting than HTML scraping.

    # Inline test fixtures
    tests:
      - desc: "PR URL should block"
        input:
          tool_name: WebFetch
          tool_input:
            url: "https://github.com/foo/bar/pull/123"
        expect: block
        contains: "gh pr view"  # optional message validation

      - desc: "repo URL should allow"
        input:
          tool_name: WebFetch
          tool_input:
            url: "https://github.com/foo/bar"
        expect: allow
```

### Pattern Matching

The `pattern` field is a regex matched against a tool-specific input field:

| Tool | Matches Against |
|------|-----------------|
| `WebFetch` | `tool_input.url` |
| `Bash` | `tool_input.command` |

Additional tools can be added to this mapping as needed.

### Conflict Detection

When merging routes from multiple sources:

- Routes are identified by name
- If two sources define the same route name, error immediately
- If two routes have patterns that could match the same input, that's allowed (first match wins, order matters)

This strict approach surfaces configuration issues during development rather than causing silent misbehavior.

## Project Structure

```
plugins/tool-routing/
├── src/
│   └── tool_routing/
│       ├── __init__.py
│       ├── cli.py           # CLI entry point and subcommands
│       ├── config.py        # YAML loading and merging
│       ├── checker.py       # Pattern matching logic
│       └── test_runner.py   # Fixture validation
├── tests/
│   ├── test_config.py       # Config loading/merging tests
│   ├── test_checker.py      # Pattern matching tests
│   └── test_cli.py          # CLI tests
├── hooks/
│   ├── hooks.json           # Claude Code hook registration
│   └── tool-routes.yaml     # Default routes shipped with plugin
├── pyproject.toml
└── README.md
```

## CLI Interface

Entry point: `tool-routing`

### Subcommands

**`tool-routing check`** (hook entry point)

Reads tool call from stdin, checks against merged routes, exits with:
- `0` - Allow tool call
- `2` - Block tool call (message printed to stderr)

```bash
# Called by hooks.json
echo '{"tool_name": "WebFetch", "tool_input": {"url": "..."}}' | tool-routing check
```

**`tool-routing test`**

Runs all inline test fixtures from merged configuration.

```bash
$ tool-routing test
plugins/tool-routing/hooks/tool-routes.yaml
  ✓ github-pr: PR URL should block
  ✓ github-pr: repo URL should allow
  ✓ git-commit-multiline: heredoc should block
  ✓ git-commit-multiline: simple -m should allow

.claude/tool-routes.yaml
  ✓ internal-api: internal URL should block

12 tests passed, 0 failed
```

**`tool-routing list`**

Shows merged routes from all sources for debugging.

```bash
$ tool-routing list
Routes (merged from 3 sources):

github-pr (from: plugins/tool-routing/hooks/tool-routes.yaml)
  tool: WebFetch
  pattern: github\.com/[^/]+/[^/]+/pull/\d+

buildkite (from: plugins/ci-cd-tools/hooks/tool-routes.yaml)
  tool: WebFetch
  pattern: buildkite\.com/[^/]+/[^/]+/builds/\d+

custom-route (from: .claude/tool-routes.yaml)
  tool: Bash
  pattern: ^my-internal-tool\s+
```

## Dependencies

### Runtime

- `pyyaml` - YAML config parsing

### Development

- `pytest` - Python unit tests
- `ruff` - Linting and formatting

### Tooling

- `uv` - Package management and script running

## Hook Registration

`hooks/hooks.json`:

```json
{
  "hooks": [
    {
      "matcher": {
        "tool_name": "WebFetch"
      },
      "hooks": [
        {
          "type": "preToolUse",
          "command": "uv run --project $CLAUDE_PLUGIN_ROOT tool-routing check"
        }
      ]
    },
    {
      "matcher": {
        "tool_name": "Bash"
      },
      "hooks": [
        {
          "type": "preToolUse",
          "command": "uv run --project $CLAUDE_PLUGIN_ROOT tool-routing check"
        }
      ]
    }
  ]
}
```

## Migration Path

1. Create `plugins/tool-routing/` with new structure
2. Convert existing `tool-routes.json` to `tool-routes.yaml`
3. Add inline tests based on existing `fixtures/` directory
4. Move routes that belong to other plugins (e.g., Buildkite → ci-cd-tools)
5. Remove tool routing code from `dev-tools`
6. Update any documentation referencing the old location

## Example Routes

### WebFetch Routes

```yaml
routes:
  github-pr:
    tool: WebFetch
    pattern: "github\\.com/[^/]+/[^/]+/pull/\\d+"
    message: |
      Use `gh pr view <number>` for GitHub PRs.

      This works for both public and private PRs and
      provides better formatting than HTML scraping.
    tests:
      - input: {tool_name: WebFetch, tool_input: {url: "https://github.com/foo/bar/pull/123"}}
        expect: block
      - input: {tool_name: WebFetch, tool_input: {url: "https://github.com/foo/bar"}}
        expect: allow

  atlassian:
    tool: WebFetch
    pattern: "https?://[^/]*\\.atlassian\\.net"
    message: |
      Use Atlassian MCP tools for Jira/Confluence.

      Call: mcp__MCPProxy__retrieve_tools
      Query: 'jira confluence atlassian issue'
    tests:
      - input: {tool_name: WebFetch, tool_input: {url: "https://mycompany.atlassian.net/browse/PROJ-123"}}
        expect: block
```

### Bash Routes

```yaml
routes:
  git-commit-multiline:
    tool: Bash
    pattern: "git\\s+commit\\s+.*(?:(?:-m\\s+[\"'][^\"']*[\"'].*-m)|(?:\\$\\(cat\\s*<<)|(?:<<[-]?\\s*['\"]?\\w+['\"]?))"
    message: |
      Don't use multiple -m flags or heredocs for git commit messages.

      For multiline commit messages:
        1. Use Write tool to create a commit message file in .tmp/
        2. Use git commit -F <file> to read from the file

      Example:
        Write(file_path=".tmp/commit-msg-YYYY-MM-DD-HHMMSS.txt", content="Title\n\nBody")
        git commit -F .tmp/commit-msg-YYYY-MM-DD-HHMMSS.txt
    tests:
      - desc: "multiple -m flags should block"
        input: {tool_name: Bash, tool_input: {command: "git commit -m \"Title\" -m \"Body\""}}
        expect: block
      - desc: "single -m should allow"
        input: {tool_name: Bash, tool_input: {command: "git commit -m \"Simple message\""}}
        expect: allow
      - desc: "-F with file should allow"
        input: {tool_name: Bash, tool_input: {command: "git commit -F .tmp/commit-msg.txt"}}
        expect: allow
```

## Future Considerations

Features explicitly deferred:

- **Priority-based conflict resolution** - Currently errors on conflicts; could add priority later if needed
- **Allow-list patterns** - Routes that explicitly allow certain inputs
- **Pattern field customization** - Currently hardcoded per tool; could add `pattern_field` if needed
- **Dynamic route registration** - Routes are currently static YAML; could support runtime registration
