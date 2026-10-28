---
name: working-with-mcp
description: Use when user mentions MCPProxy/MCP tools (e.g., "check buildkite mcp", "use slack mcp") or when you need to discover or call tools through MCPProxy - immediately checks if mcp__MCPProxy__* tools are available, suggests /mcp reconnect if missing (MCPProxy MCP server not connected), explains when to use MCP tools vs HTTP API for debugging
---

# Working with MCPProxy and MCP Tools

MCPProxy is reached two ways: as **MCP tools** (`mcp__MCPProxy__*`) when it's configured as an MCP server in Claude Code, or through its **HTTP API** (`curl http://127.0.0.1:8080/...`). Use the MCP tools. The HTTP API is only for debugging MCPProxy itself.

## First: is MCPProxy connected?

Look at the tools you already have, without running anything. MCPProxy is connected if any `mcp__MCPProxy__*` tool appears, either in your tool list or in the deferred-tools list (load deferred ones with ToolSearch before calling them). `mcp__ide__*` and other `mcp__*` prefixes are different servers.

If no `mcp__MCPProxy__*` tool appears anywhere, the MCPProxy MCP server isn't connected. Tell the user:

> "MCPProxy MCP tools aren't available in this session. Try the `/mcp` command and select MCPProxy to reconnect."

Then stop. Don't run `claude mcp list` or `mcpproxy`, don't fall back to curl, and don't try workarounds: a running MCPProxy process doesn't mean this session is connected to it, and a string of curl attempts is a sign you're avoiding that answer. MCP tools are function calls, never Bash commands.

## Core Pattern: Discover Then Call

```typescript
// 1. Search for relevant tools
mcp__MCPProxy__retrieve_tools({
  query: "keywords describing what you need",
  limit: 10
});

// 2. Examine tool schemas in results
// Look at inputSchema to understand parameters

// 3. Call the tool
mcp__MCPProxy__call_tool({
  name: "server:tool-name",  // From search results
  args_json: JSON.stringify({  // MUST be JSON string
    param1: "value",
    param2: "value"
  })
});
```

**Critical:** `args_json` must be a JSON string (use `JSON.stringify()`), not a plain object.

Newer MCPProxy versions expose `call_tool_read`, `call_tool_write`, and `call_tool_destructive` instead of a single `call_tool`; use whichever your tool list shows.

## Available MCP Tools

- `mcp__MCPProxy__retrieve_tools` - Search for tools across all upstream servers
- `mcp__MCPProxy__call_tool` - Execute a discovered tool
- `mcp__MCPProxy__upstream_servers` - Manage server configuration
- `mcp__MCPProxy__list_registries` - List available MCP registries
- `mcp__MCPProxy__search_servers` - Find new servers in registries
- `mcp__MCPProxy__read_cache` - Read paginated results
- `mcp__MCPProxy__quarantine_security` - Manage quarantined servers

## Errors that retrying won't fix

When an MCP tool call returns an error, check for these patterns. If matched, **STOP** - retrying won't help.

**Unrecoverable errors - STOP and tell the user:**

| Error Pattern | What It Means | Tell User |
|--------------|---------------|-----------|
| `authentication failed`, `OAuth/token authentication required`, `authorization required` | Upstream server needs re-auth | "Server '{name}' needs re-authentication. Run `mcpproxy auth login --server={name}` or use the MCPProxy system tray to re-authenticate." |
| `is not connected`, `is disabled` | Server offline/disabled | "Server '{name}' isn't connected. Check MCPProxy status with `mcp__MCPProxy__upstream_servers(operation='list')`." |
| `access_denied`, `insufficient_scope` | Missing permissions | "Server '{name}' lacks permissions for this operation. May need to re-authorize with additional scopes." |

**Why retrying won't help:**

These errors require user action outside of Claude:
- Re-running OAuth flow through MCPProxy CLI or system tray
- Fixing server configuration
- Granting additional permissions

**Don't:**
- Retry the same tool with different parameters
- Try other tools on the same server (they'll fail too)
- Fall back to WebFetch/curl (won't have auth either)

## Debugging MCPProxy Connection Issues

If MCPProxy itself isn't working properly (servers won't connect, Docker issues, etc.), you can use these quick checks:

### Quick Health Check

```bash
# 1. Is mcpproxy running?
ps aux | grep mcpproxy | grep -v grep

# 2. Get API key
grep '"api_key"' ~/.mcpproxy/mcp_config.json

# 3. Check server status
curl -s "http://127.0.0.1:8080/api/v1/servers?apikey=YOUR_KEY" | python3 -m json.tool

# 4. Check for recent errors
tail -50 ~/Library/Logs/mcpproxy/main.log | grep -i error
```

**Key status fields to check:**
- `connected`: Boolean - is the server connected?
- `status`: String - current state (connecting, ready, error)
- `last_error`: String - most recent error message
- `tool_count`: Number - how many tools available

### Common MCPProxy Issues

#### "the input device is not a TTY" (Docker servers)
**Fix:** Add `"isolation": {"enabled": false}` to the Docker-based server config.

#### "unexpected argument found" (uvx/npx servers)
**Fix:** Put package name as first arg: `["mcp-server-name", "--arg", "value"]`

#### "Invalid or missing API key" after restart
**Fix:** Check `echo $MCPPROXY_API_KEY` - environment variable overrides config file.

### Restart MCPProxy

```bash
pkill mcpproxy
sleep 2
open /Applications/mcpproxy.app  # macOS
# OR
mcpproxy &  # Linux/headless
```
