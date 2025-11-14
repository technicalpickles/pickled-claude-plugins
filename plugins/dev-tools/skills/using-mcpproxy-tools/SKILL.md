---
name: using-mcpproxy-tools
description: Use when MCPProxy is configured and you need to discover or call tools - checks if mcp__MCPProxy__ tools are available, suggests /mcp reconnect if missing, explains when to use MCP tools vs HTTP API for debugging
---

# Using MCPProxy Tools

## Overview

MCPProxy can be accessed two ways:
1. **MCP Tools** (`mcp__MCPProxy__*`) - When MCPProxy is configured as an MCP server in Claude Code
2. **HTTP API** (`curl http://localhost:8080/...`) - For debugging MCPProxy itself or when MCP tools unavailable

**This skill is for #1**. For #2, use `debugging-tools:mcpproxy-debug`.

## When to Use This Skill

**Use when:**
- You need to discover what tools MCPProxy exposes
- You want to call a tool through MCPProxy
- MCPProxy is configured but you're not sure if MCP tools are available

**Do NOT use when:**
- Debugging MCPProxy itself (connection failures, config issues) → Use `debugging-tools:mcpproxy-debug`
- MCPProxy not configured at all → Can't use either approach

## Quick Reference

| Task | Check This First | Then Use |
|------|------------------|----------|
| Discover tools | Are `mcp__MCPProxy__*` in tool list? | If yes: `mcp__MCPProxy__retrieve_tools`<br>If no: Suggest `/mcp` reconnect |
| Call a tool | Are `mcp__MCPProxy__*` in tool list? | If yes: `mcp__MCPProxy__call_tool`<br>If no: Suggest `/mcp` reconnect |
| Debug MCPProxy | N/A | Use `debugging-tools:mcpproxy-debug` skill |

## Step-by-Step: Check Tool Availability

### Step 1: Check Your Tool List

Look for tools prefixed with `mcp__MCPProxy__`:
- `mcp__MCPProxy__retrieve_tools`
- `mcp__MCPProxy__call_tool`
- `mcp__MCPProxy__upstream_servers`
- `mcp__MCPProxy__list_registries`
- `mcp__MCPProxy__search_servers`
- `mcp__MCPProxy__read_cache`
- `mcp__MCPProxy__quarantine_security`

### Step 2: If Tools Are Available → Use Them

```typescript
// Search for tools
mcp__MCPProxy__retrieve_tools({
  query: "slack post message",
  limit: 10
})

// Call a tool
mcp__MCPProxy__call_tool({
  name: "slack:post_message",
  args_json: JSON.stringify({
    channel: "#general",
    message: "Hello"
  })
})
```

### Step 3: If Tools Are NOT Available → Reconnect

Tell the user:
> "MCPProxy MCP tools aren't available in this session. Try the `/mcp` command and select MCPProxy to reconnect."

**Don't fall back to HTTP API** - that's for debugging MCPProxy, not for using it.

## Core Pattern: Discover Then Call

```typescript
// 1. Search for relevant tools
const tools = mcp__MCPProxy__retrieve_tools({
  query: "keywords describing what you need"
});

// 2. Examine tool schemas in results
// Look at inputSchema to understand parameters

// 3. Call the tool
mcp__MCPProxy__call_tool({
  name: "server:tool-name",  // From search results
  args_json: JSON.stringify({
    param1: "value",
    param2: "value"
  })
});
```

**Critical:** `args_json` must be a JSON string (use `JSON.stringify()`), not a plain object.

## Common Mistakes

### ❌ Invoking MCP tools as bash commands

```bash
# WRONG - Don't use MCP tools as bash commands
mcp__MCPProxy__retrieve_tools --query "slack tools"
mcp__MCPProxy__call_tool --name slack:post_message
```

**Why wrong:** `mcp__MCPProxy__*` are MCP tools (functions), not bash commands.

### ✅ Invoke as MCP tools (functions)

```typescript
// CORRECT - Call as MCP tool
mcp__MCPProxy__retrieve_tools({
  query: "slack tools"
})

mcp__MCPProxy__call_tool({
  name: "slack:post_message",
  args_json: JSON.stringify({ channel: "#general" })
})
```

**How to tell the difference:**
- **MCP tools**: `mcp__server__tool` pattern → Call as function with object parameter
- **Bash commands**: `mcpproxy`, `claude`, `docker` → Run via Bash tool with flags
- **Never use Bash tool to run MCP tools**

### ❌ Assuming tools don't exist

```
// Agent tries:
mcp__MCPProxy__retrieve_tools(...)

// Gets error:
"No such tool available: mcp__MCPProxy__retrieve_tools"

// Agent concludes:
"The tool doesn't exist. I'll use the HTTP API instead."

// WRONG! The tool exists, but MCP connection isn't established.
```

### ✅ Recognizing connection issue

```
// Agent tries:
mcp__MCPProxy__retrieve_tools(...)

// Gets error:
"No such tool available"

// Agent recognizes:
"MCPProxy MCP tools aren't available. The MCP server isn't connected."

// Agent suggests:
"Try `/mcp` and select MCPProxy to reconnect."
```

### ❌ Using HTTP API when MCP tools should work

```bash
# WRONG - Don't do this when MCP tools should be available
curl http://127.0.0.1:8080/api/v1/tools?apikey=...
```

**Why wrong:** HTTP API is for debugging MCPProxy itself, not for normal tool usage. If MCPProxy is configured as an MCP server, use MCP tools.

### ✅ Use MCP tools when available

```typescript
// CORRECT - Use MCP tools
mcp__MCPProxy__retrieve_tools({
  query: "search query"
})
```

## Differentiation Guide

| Scenario | Use This Skill | Use mcpproxy-debug |
|----------|---------------|---------------------|
| Discover available tools | ✅ Yes (if `mcp__MCPProxy__*` available) | ❌ No |
| Call a tool through MCPProxy | ✅ Yes (if `mcp__MCPProxy__*` available) | ❌ No |
| MCPProxy won't start | ❌ No | ✅ Yes |
| Connection errors | ❌ No | ✅ Yes |
| Docker isolation issues | ❌ No | ✅ Yes |
| Config file problems | ❌ No | ✅ Yes |
| `mcp__MCPProxy__*` tools missing | ✅ Yes (suggest `/mcp`) | ⚠️  Maybe (if debugging why) |

## Troubleshooting

### Problem: `mcp__MCPProxy__retrieve_tools` says "No such tool"

**Diagnosis:** MCP connection to MCPProxy isn't established

**Solution:**
1. Tell user: "MCPProxy MCP tools aren't available. Try `/mcp` command."
2. User runs `/mcp` and selects MCPProxy to reconnect
3. Try `mcp__MCPProxy__retrieve_tools` again

**Don't:** Fall back to HTTP API

### Problem: Should I use HTTP API or MCP tools?

**Decision tree:**
1. Are `mcp__MCPProxy__*` tools in your tool list?
   - **Yes** → Use MCP tools (this skill)
   - **No** → Is MCPProxy configured as MCP server?
     - **Yes** → Suggest `/mcp` reconnect
     - **No** → Use HTTP API (mcpproxy-debug skill)

## Red Flags - STOP Immediately

**If you think any of these, STOP:**
- "I'll run `mcp__MCPProxy__retrieve_tools` as a bash command"
- "The tool name looks like a command, so I'll use Bash tool"
- "The `mcp__MCPProxy__*` tools don't exist, I'll use curl"
- "HTTP API is simpler, I'll use that"
- "I can access MCPProxy via HTTP so that's fine"
- "The tool error means MCPProxy isn't running"
- "Let me try a different way to parse the HTTP API response"
- "Maybe if I use Python/jq/grep it will work"

**The HTTP API spiral:**
If you find yourself making multiple curl attempts with different parsing strategies, STOP. This is a sign you're avoiding the real problem: MCP isn't connected.

**Reality:**
- `mcp__MCPProxy__*` tools exist when MCP connection is established
- Missing tools = connection issue, not "tools don't exist"
- HTTP API is for debugging MCPProxy, not for normal usage
- Running ≠ Connected. Process can run but MCP not connected.

## Real-World Examples

### Example 1: The HTTP API Spiral (5 Attempts!)

**Actual failure from conversation:**

```
Agent tried:
mcp__MCPProxy__call_tool({
  server_name: "redash",
  tool_name: "execute_adhoc_query",
  ...
})

Error: "No such tool available: mcp__MCPProxy__call_tool"

Agent's spiral into HTTP API (made 5 attempts!):
1. curl http://127.0.0.1:8080/api/v1/servers/redash/tools?apikey=...
2. curl http://127.0.0.1:8080/api/v1/tools?apikey=... | python3 -c "parse json"
3. curl http://127.0.0.1:8080/api/v1/tools?apikey=... | python3 -m json.tool | grep
4. curl http://127.0.0.1:8080/api/v1/tools?apikey=... | grep (without json.tool)
5. Python script wrapping curl to parse differently

User had to interrupt after 5th attempt.

WRONG! Agent got stuck trying different parsing strategies instead of
recognizing the real problem: MCP not connected.
```

**Correct response:**

```
Agent tried:
mcp__MCPProxy__call_tool(...)

Error: "No such tool available"

Agent recognizes:
"MCPProxy MCP tools aren't available. The MCP connection isn't established."

Agent suggests:
"Try the /mcp command and select MCPProxy to reconnect.
Once reconnected, you'll have access to mcp__MCPProxy__call_tool."
```

### Example 2: Wrong Rationalization

**Actual failure from different conversation:**

```
Agent tried: mcp__MCPProxy__retrieve_tools
Error: "No such tool available"

Agent's rationalization:
"The mcp__MCPProxy__retrieve_tools tool doesn't exist -
the glean tools are accessed through the MCPProxy API"
→ Falls back to HTTP API

WRONG! Tool exists, just not connected.
```

**Correct response:**

```
Agent tried: mcp__MCPProxy__retrieve_tools
Error: "No such tool available"

Agent recognizes:
"MCPProxy MCP tools should exist but aren't available.
This means the MCP server isn't connected."

Agent suggests:
"Use /mcp command to reconnect to MCPProxy."
```

## Summary

1. **Check** if `mcp__MCPProxy__*` tools are in your tool list
2. **If yes** → Use MCP tools (`mcp__MCPProxy__retrieve_tools`, `mcp__MCPProxy__call_tool`)
3. **If no** → Suggest user run `/mcp` to reconnect
4. **Never** fall back to HTTP API when MCP tools should exist
5. **HTTP API** is only for debugging MCPProxy itself (different skill)
