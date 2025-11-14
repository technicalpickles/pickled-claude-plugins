---
name: using-mcpproxy-tools
description: Use when MCPProxy is configured and you need to discover or call tools - checks if mcp__MCPProxy__ tools are available, suggests /mcp reconnect if missing, explains when to use MCP tools vs HTTP API for debugging
---

# Using MCPProxy Tools

## Overview

MCPProxy can be accessed two ways:
1. **MCP Tools** (`mcp__MCPProxy__*`) - When MCPProxy is configured as an MCP server in Claude Code
2. **HTTP API** (`curl http://localhost:8080/...`) - For debugging MCPProxy itself

**This skill is for #1.** For #2, use `debugging-tools:mcpproxy-debug`.

## Core Decision Tree

This is your decision tree. Use it every time:

```
Are mcp__MCPProxy__* tools in your tool list?
│
├─ YES → Use MCP tools
│         ├─ Discover: mcp__MCPProxy__retrieve_tools
│         └─ Call: mcp__MCPProxy__call_tool
│
└─ NO → Is MCPProxy configured as MCP server?
          ├─ YES → Suggest: "Try /mcp command to reconnect"
          └─ NO → Can't use either approach
```

**Never fall back to HTTP API when MCP tools should exist.** Missing tools = connection issue, not "tools don't exist."

## When to Use This Skill

**Use when:**
- You need to discover what tools MCPProxy exposes
- You want to call a tool through MCPProxy
- MCPProxy is configured but you're not sure if MCP tools are available

**Do NOT use when:**
- Debugging MCPProxy itself (connection failures, config issues) → Use `debugging-tools:mcpproxy-debug`
- MCPProxy not configured at all → Can't use either approach

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

## Available MCP Tools

- `mcp__MCPProxy__retrieve_tools` - Search for tools across all upstream servers
- `mcp__MCPProxy__call_tool` - Execute a discovered tool
- `mcp__MCPProxy__upstream_servers` - Manage server configuration
- `mcp__MCPProxy__list_registries` - List available MCP registries
- `mcp__MCPProxy__search_servers` - Find new servers in registries
- `mcp__MCPProxy__read_cache` - Read paginated results
- `mcp__MCPProxy__quarantine_security` - Manage quarantined servers

## Quick Reference

| Task | Check This First | Then Use |
|------|------------------|----------|
| Discover tools | Are `mcp__MCPProxy__*` in tool list? | If yes: `retrieve_tools`<br>If no: Suggest `/mcp` |
| Call a tool | Are `mcp__MCPProxy__*` in tool list? | If yes: `call_tool`<br>If no: Suggest `/mcp` |
| Debug MCPProxy | N/A | Use `debugging-tools:mcpproxy-debug` |

## If MCP Tools Are Missing

When `mcp__MCPProxy__*` tools are not in your tool list:

**Tell the user:**
> "MCPProxy MCP tools aren't available in this session. Try the `/mcp` command and select MCPProxy to reconnect."

**Do NOT:**
- Fall back to HTTP API (that's for debugging MCPProxy)
- Assume the tools don't exist
- Try bash commands
- Make multiple curl attempts

**Reality:** The tools exist when MCP connection is established. Missing tools = connection issue.

## Top 3 Common Mistakes

### 1. Invoking MCP Tools as Bash Commands

```bash
# ❌ WRONG - MCP tools are not bash commands
mcp__MCPProxy__retrieve_tools --query "slack tools"
```

```typescript
// ✅ CORRECT - Call as MCP tool (function)
mcp__MCPProxy__retrieve_tools({
  query: "slack tools"
})
```

**How to tell the difference:**
- `mcp__server__tool` pattern → MCP tool (function call)
- `mcpproxy`, `docker` → Bash command (via Bash tool)

### 2. Using HTTP API Instead of MCP Tools

```bash
# ❌ WRONG - Don't do this when MCP tools should work
curl http://127.0.0.1:8080/api/v1/tools?apikey=...
```

```typescript
// ✅ CORRECT - Use MCP tools
mcp__MCPProxy__retrieve_tools({query: "search query"})
```

**HTTP API is only for debugging MCPProxy itself.**

### 3. Falling Into the HTTP API Spiral

```
Agent tries: mcp__MCPProxy__call_tool(...)
Gets error: "No such tool available"
Agent makes:
1. curl attempt with python parsing
2. curl attempt with json.tool
3. curl attempt with grep
4. Python script wrapping curl
5. Different parsing strategy...
```

**STOP!** Multiple curl attempts = you're avoiding the real problem: MCP not connected. Suggest `/mcp` instead.

## Red Flags - STOP Immediately

If you think any of these thoughts, **STOP**:

- "I'll run `mcp__MCPProxy__retrieve_tools` as a bash command"
- "The `mcp__MCPProxy__*` tools don't exist, I'll use curl"
- "HTTP API is simpler, I'll use that"
- "Let me try a different way to parse the HTTP response"
- "Maybe if I use Python/jq/grep it will work"
- "The tool error means MCPProxy isn't running"

**Reality:**
- `mcp__MCPProxy__*` tools exist when MCP connection is established
- Missing tools = connection issue, not "tools don't exist"
- HTTP API is for debugging MCPProxy, not for normal usage
- Running ≠ Connected. Process can run but MCP not connected.

For detailed examples of these mistakes, see `references/common-mistakes.md`.

## Differentiation Guide

| Scenario | This Skill | mcpproxy-debug |
|----------|-----------|----------------|
| Discover available tools | ✅ (if MCP connected) | ❌ |
| Call a tool through MCPProxy | ✅ (if MCP connected) | ❌ |
| MCPProxy won't start | ❌ | ✅ |
| Connection errors | ❌ | ✅ |
| Docker isolation issues | ❌ | ✅ |
| Config file problems | ❌ | ✅ |
| MCP tools missing | ✅ (suggest `/mcp`) | ⚠️ (if debugging why) |

## References - Deep Dives

Load these on-demand when you need detailed examples:

### `references/common-mistakes.md`
**When to read:** You're about to fall back to HTTP API or invoke MCP tools as bash commands

**Contains:**
- Detailed ❌/✅ examples with explanations
- How to distinguish MCP tools from bash commands
- When HTTP API is appropriate (spoiler: almost never for you)
- Detailed comparison of approaches

### `references/troubleshooting-guide.md`
**When to read:** MCP tools aren't working and you need detailed diagnosis

**Contains:**
- Step-by-step troubleshooting workflow
- Real-world failure examples (the HTTP API spiral)
- How to recognize connection issues vs other problems
- Complete walkthrough of "/mcp reconnect" workflow

## When to Load References

**Don't load references preemptively.** Use this workflow:

1. Check if `mcp__MCPProxy__*` tools are available
2. If yes → Use them (discover then call pattern)
3. If no → Suggest `/mcp` reconnect
4. If unsure about approach → Read `references/common-mistakes.md`
5. If tools not working → Read `references/troubleshooting-guide.md`

**Why:** Loading all references upfront = 2,500+ tokens. Progressive disclosure keeps it lean (~1,200 initially, +1,500 on-demand).

## Summary

**The capability:** Use MCPProxy's tool discovery to find and call tools across all upstream MCP servers.

**The pattern:**
1. Check if `mcp__MCPProxy__*` tools exist
2. If yes → Use them (discover then call)
3. If no → Suggest `/mcp` reconnect
4. Never fall back to HTTP API

**Result:** Fast tool usage with clear error handling. ~1,200 tokens initially, load references only when needed.
