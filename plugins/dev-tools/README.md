# dev-tools Plugin

Developer productivity tools and utilities.

## Skills

### working-in-scratch-areas

Use when creating one-off scripts, debug tools, analysis reports, or temporary documentation - ensures work is saved to persistent .scratch areas with proper documentation, organization, and executable patterns.

## Hooks

### Tool Routing Hook

Automatically suggests better tools when Claude tries to WebFetch certain services.

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

**Files:**
- `hooks/tool-routes.json` - Service patterns and messages (edit this)
- `hooks/check-tool-routing.py` - Hook implementation (no need to edit)
- `hooks/hooks.json` - Hook registration (automatic)
