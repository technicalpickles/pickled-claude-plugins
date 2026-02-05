# mcpproxy Plugin

MCP server management and integration tools.

## Skills

### working-with-mcp

Use when working with MCPProxy and MCP tools - detecting connection status, discovering tools, and managing MCP servers.

**Key capabilities:**
- Detect if MCPProxy MCP server is connected
- Discover tools across upstream MCP servers
- Call tools through MCPProxy
- Manage upstream server configuration
- Troubleshoot connection issues

**Core pattern:**
1. Check if `mcp__MCPProxy__*` tools are available
2. If yes → Use them (discover then call)
3. If no → Suggest `/mcp` reconnect
4. Never fall back to HTTP API for normal usage

## Installation

```bash
/plugin install mcpproxy@pickled-claude-plugins
```
