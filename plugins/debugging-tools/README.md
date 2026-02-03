# debugging-tools Plugin

Debugging utilities and diagnostics tools for development workflows.

## Skills

### mcpproxy-debug

Use when user mentions MCPProxy/MCP tools or when you need to discover or call tools through MCPProxy. Immediately checks if `mcp__MCPProxy__*` tools are available, suggests `/mcp reconnect` if missing, and explains when to use MCP tools vs HTTP API for debugging.

**Key capabilities:**
- Detect MCPProxy connection status
- Discover available MCP tools
- Call tools through MCPProxy
- Troubleshoot MCP connection issues
- Guide usage of MCP tools vs HTTP API

## Installation

```bash
/plugin install debugging-tools@pickled-claude-plugins
```
