# dev-tools Plugin

Developer productivity tools and utilities.

## Skills

### working-in-scratch-areas

Use when creating one-off scripts, debug tools, analysis reports, or temporary documentation - ensures work is saved to persistent .scratch areas with proper documentation, organization, and executable patterns.

## Hooks

### Tool Routing Hook

Automatically suggests better tools when Claude tries to WebFetch certain services.

**📖 See [docs/tool-routing-hook.md](docs/tool-routing-hook.md) for design principles and implementation details.**

**What it does:**
- Intercepts WebFetch calls before execution
- Checks URLs against configured patterns
- Blocks and suggests alternatives for matched services

**Configured services:**
- **Atlassian (Jira/Confluence)** → Suggests MCP tools via `mcp__MCPProxy__retrieve_tools`
- **GitHub PRs** → Suggests `gh pr view <number>` for both public and private PRs

**Benefits:**
- MCP tools provide authentication and structured data
- `gh pr view` works for private repos (WebFetch doesn't)
- Better formatting than HTML scraping
- Automatic enforcement (doesn't rely on Claude remembering)

**To add a service:**

Edit `hooks/tool-routes.json`:

```json
{
  "routes": {
    "your-service": {
      "pattern": "your-regex-pattern",
      "message": "Your helpful message here"
    }
  }
}
```

**Example - Adding Linear:**

```json
"linear": {
  "pattern": "linear\\.app/[^/]+/issue",
  "message": "Use Linear MCP tools for issue access.\n\nCall: mcp__MCPProxy__retrieve_tools\nQuery: 'linear issue project'"
}
```

**Debug Mode:**

By default, the hook is silent (no warnings). Enable debug output:

```bash
export TOOL_ROUTING_DEBUG=1
```

Debug mode shows:
- Config loading status
- Which routes are being checked
- Match results
- Why tools are allowed/blocked

**Requirements:**

The hook uses `uv` for automatic Python version management:
- `uv` automatically installs Python >=3.9 if needed
- No external dependencies (uses Python stdlib only)
- Inline script metadata tracks dependencies if added later

Install uv: https://docs.astral.sh/uv/

**Testing:**

Run tests from the dev-tools directory:
```bash
cd plugins/dev-tools
uv run hooks/test_tool_routing.py
```

Run with debug output:
```bash
TOOL_ROUTING_DEBUG=1 uv run hooks/test_tool_routing.py
```

Tests verify:
- Atlassian URLs are blocked with MCP tool suggestion
- GitHub PR URLs are blocked with gh pr view suggestion
- Other URLs pass through normally
- Fail-open behavior for errors

**Files:**
- `hooks/tool-routes.json` - Service patterns and messages (edit this)
- `hooks/check_tool_routing.py` - Hook implementation with PEP 723 inline script metadata
- `hooks/hooks.json` - Hook registration (uses `uv run`)
- `hooks/test_tool_routing.py` - Test suite
