# Tool Routing Plugin

Intercepts tool calls and suggests better alternatives. When Claude tries to use a tool in a suboptimal way, tool-routing blocks the call and explains what to do instead.

## Installation

Add to your Claude Code plugins:

```bash
claude plugin add pickled-claude-plugins/tool-routing
```

## Quick Example

This route blocks GitHub PR URLs and suggests using the `gh` CLI:

```yaml
# hooks/tool-routes.yaml
routes:
  github-pr:
    tool: WebFetch
    pattern: "github\\.com/[^/]+/[^/]+/pull/\\d+"
    message: |
      Use `gh pr view <number>` for GitHub PRs.

      This works for both public and private PRs and
      provides better formatting than HTML scraping.
    tests:
      - input:
          tool_name: WebFetch
          tool_input:
            url: "https://github.com/foo/bar/pull/123"
        expect: block
```

## Route Sources

Routes are discovered from all enabled plugins that declare routes in their manifest:

1. Each plugin declares route files in `.claude-plugin/routes.json`
2. Discovery uses `claude plugin list --json` to find enabled plugins
3. Route files are loaded and merged from each plugin's manifest

See [Route Discovery](docs/route-discovery.md) for details.

## CLI

```bash
cd plugins/tool-routing

# Check a tool call (hook entry point)
uv run tool-routing check

# Run inline tests
uv run tool-routing test

# List all routes
uv run tool-routing list
```

See [CLI Reference](docs/cli-reference.md) for full documentation.

## Documentation

- [Writing Routes](docs/writing-routes.md) - How to create routes and tests
- [Route Discovery](docs/route-discovery.md) - Multi-source merging and configuration
- [CLI Reference](docs/cli-reference.md) - Command details and exit codes
- [Architecture](docs/architecture.md) - Internal design (for contributors)

## Default Routes

The plugin ships with routes for common patterns:

| Route | Tool | What it blocks |
|-------|------|----------------|
| `github-pr` | WebFetch | GitHub PR URLs → use `gh pr view` |
| `atlassian` | WebFetch | Jira/Confluence URLs → use MCP tools |
| `buildkite` | WebFetch | Build URLs → use MCP tools |
| `bash-mcp-cli` | Bash | `mcp` CLI commands → use tool calls |
| `bash-mcp-tool` | Bash | MCP tool names as commands |
| `git-commit-multiline` | Bash | Heredocs in commits → use Write + `-F` |
| `gh-pr-create-multiline` | Bash | Heredocs in PRs → use Write + `--body-file` |
| `bash-cat-heredoc` | Bash | Cat heredocs → use Write tool |
| `bash-echo-chained` | Bash | Chained echo → output directly |
| `bash-echo-redirect` | Bash | Echo redirects → use Write tool |

## License

MIT
