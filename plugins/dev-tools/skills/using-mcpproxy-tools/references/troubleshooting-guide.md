# Troubleshooting Guide - Step-by-Step

**When to use this reference:** MCP tools aren't working and you need detailed diagnosis.

This reference provides systematic troubleshooting workflows for issues with MCPProxy MCP tools.

## Problem Categories

### Category 1: MCP Tools Not Available

**Symptoms:**
- `mcp__MCPProxy__*` tools not in tool list
- Error: "No such tool available: mcp__MCPProxy__retrieve_tools"
- Error: "No such tool available: mcp__MCPProxy__call_tool"

**Not symptoms of this category:**
- MCPProxy won't start (see `debugging-tools:mcpproxy-debug`)
- Server connection failures (see `debugging-tools:mcpproxy-debug`)
- Configuration issues (see `debugging-tools:mcpproxy-debug`)

### Category 2: MCP Tool Call Failures

**Symptoms:**
- MCP tools exist in tool list
- Tool calls return errors
- Tool calls timeout
- Tool calls return unexpected results

## Troubleshooting Workflow: Category 1 (Tools Not Available)

This is the most common issue: MCP tools should exist but aren't in your tool list.

### Step 1: Verify Tools Are Actually Missing

Check your available tools:

```typescript
// Look through your tool list
// Do you see any tools matching these patterns?
mcp__MCPProxy__retrieve_tools
mcp__MCPProxy__call_tool
mcp__MCPProxy__upstream_servers
mcp__MCPProxy__list_registries
mcp__MCPProxy__search_servers
mcp__MCPProxy__read_cache
mcp__MCPProxy__quarantine_security
```

**If you see ANY of these tools:**
- Skip to Category 2 (tool call failures)
- The tools are available, issue is elsewhere

**If you see NONE of these tools:**
- Continue with this workflow
- This is an MCP connection issue

### Step 2: Understand the Root Cause

**Why tools are missing:**

MCPProxy must be configured as an MCP server in Claude Code's configuration. When configured, it exposes tools via MCP protocol.

**What breaks the connection:**
1. Claude Code session started before MCPProxy was added to config
2. MCP connection was established but dropped
3. MCPProxy restarted but MCP connection not re-established
4. Configuration changed and session not refreshed

**Key insight:** MCPProxy process can be running (HTTP API accessible) while MCP connection is broken (MCP tools unavailable).

### Step 3: Diagnose Connection State

**Check 1: Is MCPProxy running?**

```bash
ps aux | grep mcpproxy | grep -v grep
```

**Expected:** Process is running
**If not running:** Start MCPProxy (see `debugging-tools:mcpproxy-debug`)

**Check 2: Is HTTP API accessible?**

```bash
# Get API key
API_KEY=$(grep '"api_key"' ~/.mcpproxy/mcp_config.json | cut -d'"' -f4)

# Test HTTP API
curl -s "http://127.0.0.1:8080/api/v1/servers?apikey=$API_KEY" | head -20
```

**Expected:** JSON response with server list
**If not accessible:** MCPProxy isn't running or has issues (see `debugging-tools:mcpproxy-debug`)

**Check 3: Is MCPProxy configured in Claude Code?**

```bash
# Check Claude Code MCP config
cat ~/.claude/config.json | python3 -m json.tool | grep -i mcpproxy
```

**Expected:** MCPProxy appears in config
**If not configured:** MCPProxy never added to Claude Code

**Conclusion from checks:**

| MCPProxy Running | HTTP API Works | In Claude Config | Issue |
|------------------|----------------|------------------|-------|
| ✅ | ✅ | ✅ | MCP connection not established |
| ✅ | ✅ | ❌ | Not configured in Claude Code |
| ✅ | ❌ | ✅ | MCPProxy has issues |
| ❌ | ❌ | ✅ | MCPProxy not running |

**For all cases:** The solution is to reconnect via `/mcp` command.

### Step 4: Reconnect via /mcp Command

**Tell the user:**

> "MCPProxy MCP tools aren't available in this session. To reconnect:
>
> 1. Type `/mcp` command
> 2. Select 'MCPProxy' from the list
> 3. Connection will be re-established
> 4. You'll then have access to all `mcp__MCPProxy__*` tools
>
> Once reconnected, try your operation again."

**What /mcp does:**
1. Shows list of configured MCP servers
2. User selects MCPProxy
3. Claude Code establishes MCP connection
4. MCPProxy tools become available in tool list

**After reconnection:**
- Check tool list again
- `mcp__MCPProxy__*` tools should now appear
- Can now use MCP tools normally

### Step 5: Verify Reconnection

After user runs `/mcp` and selects MCPProxy:

```typescript
// Try using an MCP tool
mcp__MCPProxy__retrieve_tools({
  query: "test",
  limit: 5
})

// If this works: Connection successful
// If this fails with same error: Connection still broken
```

**If still broken after /mcp:**
- This is a deeper MCPProxy issue
- Switch to `debugging-tools:mcpproxy-debug` skill
- Investigate MCPProxy configuration and logs

## Troubleshooting Workflow: Category 2 (Tool Call Failures)

MCP tools exist but calling them fails.

### Step 1: Identify the Error Type

**Error Type A: "No such tool available: SERVER:TOOL_NAME"**

Example:
```
Error: No such tool available: slack:post_message
```

**Cause:** The upstream server (slack) isn't connected to MCPProxy.

**Solution:** Use `debugging-tools:mcpproxy-debug` to diagnose why the upstream server isn't connected.

**Error Type B: Tool returns error message**

Example:
```
{
  "error": "Invalid channel ID",
  "details": "..."
}
```

**Cause:** Tool executed but failed due to bad parameters or server-side issue.

**Solution:** Check tool's inputSchema and fix parameters.

**Error Type C: Tool times out**

Example:
```
Error: Tool execution timed out after 30 seconds
```

**Cause:** Upstream server is slow or hung.

**Solution:** Use `debugging-tools:mcpproxy-debug` to check server logs.

**Error Type D: Tool returns unexpected format**

Example:
```
Expected JSON but got HTML error page
```

**Cause:** Upstream server crashed or returned error.

**Solution:** Use `debugging-tools:mcpproxy-debug` to check server logs.

### Step 2: Check Tool Schema

Before calling a tool, verify its schema:

```typescript
// Retrieve tools and examine schema
mcp__MCPProxy__retrieve_tools({
  query: "tool name",
  limit: 5
})

// Response includes inputSchema
// Example:
{
  "name": "slack:post_message",
  "inputSchema": {
    "type": "object",
    "properties": {
      "channel": {"type": "string", "description": "Channel ID"},
      "message": {"type": "string", "description": "Message text"}
    },
    "required": ["channel", "message"]
  }
}
```

**Verify:**
- You're using correct parameter names
- Required parameters are provided
- Parameter types match schema
- `args_json` is a JSON string (use `JSON.stringify()`)

### Step 3: Test with Minimal Parameters

Try calling the tool with only required parameters:

```typescript
// Minimal example
mcp__MCPProxy__call_tool({
  name: "slack:post_message",
  args_json: JSON.stringify({
    channel: "#general",
    message: "test"
  })
})
```

**If minimal call works:**
- Issue is with optional parameters
- Add parameters one by one to identify problem

**If minimal call fails:**
- Issue is with required parameters or server-side
- Check parameter values
- Use `debugging-tools:mcpproxy-debug` to check server logs

### Step 4: Check Upstream Server Status

Verify the upstream server is connected:

```typescript
// List all servers
mcp__MCPProxy__upstream_servers({
  operation: "list"
})

// Look for your server in results
// Check these fields:
{
  "name": "slack",
  "connected": true,  // Should be true
  "status": "ready",   // Should be ready
  "tool_count": 15     // Should be > 0
}
```

**If server not connected:**
- Use `debugging-tools:mcpproxy-debug` to diagnose
- See `references/connection-failures.md` in that skill

**If server connected but tool fails:**
- Issue is with tool call, not connection
- Continue troubleshooting tool parameters

## Real-World Example: The HTTP API Spiral

This is a real failure from a conversation. The agent made 5 attempts with HTTP API instead of recognizing the connection issue.

### What Happened

**Initial attempt:**
```typescript
mcp__MCPProxy__call_tool({
  name: "redash:execute_adhoc_query",
  args_json: JSON.stringify({...})
})
```

**Error:**
```
Error: No such tool available: mcp__MCPProxy__call_tool
```

**Agent's response (WRONG):**

Instead of recognizing MCP connection issue, agent spiraled into HTTP API:

1. **Attempt 1:** `curl http://127.0.0.1:8080/api/v1/servers/redash/tools?apikey=...`
2. **Attempt 2:** `curl ... | python3 -c "import json; parse..."`
3. **Attempt 3:** `curl ... | python3 -m json.tool | grep`
4. **Attempt 4:** `curl ... | grep` (without json.tool)
5. **Attempt 5:** Python script wrapping curl with different parsing

**User had to interrupt after 5th attempt.**

### What Should Have Happened

**Initial attempt:**
```typescript
mcp__MCPProxy__call_tool({...})
```

**Error:**
```
Error: No such tool available: mcp__MCPProxy__call_tool
```

**Correct response:**
```
"MCPProxy MCP tools aren't available in this session.
This means the MCP connection isn't established.

Try the /mcp command and select MCPProxy to reconnect.
Once reconnected, you'll have access to mcp__MCPProxy__call_tool."
```

**Result:**
- User runs `/mcp`, selects MCPProxy
- Connection established
- Tools available
- Problem solved in one step

### Lesson

**Signs you're entering the HTTP API spiral:**
1. First MCP tool call fails with "No such tool available"
2. You think "let me try the HTTP API"
3. First curl attempt doesn't give what you need
4. You think "maybe different parsing will work"
5. You make second curl attempt
6. **← YOU ARE NOW IN THE SPIRAL**

**How to avoid:**
1. MCP tool call fails with "No such tool available"
2. Recognize: This is a connection issue
3. Suggest: `/mcp` reconnect
4. **← PROBLEM SOLVED, NO SPIRAL**

## Common Questions

### Q: How do I know if MCP tools are available?

**A:** Check your tool list for `mcp__MCPProxy__*` tools. If you see any of them, MCP is connected.

### Q: MCPProxy is running but tools aren't available. Why?

**A:** Running ≠ Connected. The process can run (HTTP API works) while MCP connection is broken (MCP tools unavailable). Use `/mcp` to reconnect.

### Q: Can I use HTTP API instead of MCP tools?

**A:** No. HTTP API is for debugging MCPProxy itself, not for normal usage. Always use MCP tools from Claude Code.

### Q: I ran /mcp but tools still aren't available. What now?

**A:** This indicates a deeper MCPProxy issue. Switch to `debugging-tools:mcpproxy-debug` skill to investigate MCPProxy configuration and logs.

### Q: How do I check if a specific upstream server is connected?

**A:** Use `mcp__MCPProxy__upstream_servers({operation: "list"})` and check the `connected` field for your server.

### Q: Tool call returns "No such tool available: SERVER:TOOL". What does this mean?

**A:** The upstream server (SERVER) isn't connected to MCPProxy. Use `debugging-tools:mcpproxy-debug` to diagnose the upstream server connection.

### Q: Should I check if mcpproxy process is running?

**A:** No. Just check if MCP tools are available. Process running ≠ MCP connected.

## Summary Decision Tree

```
Need to use MCPProxy tools
│
├─ Are mcp__MCPProxy__* in tool list?
│  │
│  ├─ YES → Tools are available
│  │        ├─ Tool call succeeds → Working correctly
│  │        └─ Tool call fails → Troubleshoot tool call (Category 2)
│  │
│  └─ NO → Tools are NOT available
│           ├─ Tell user: "Try /mcp command to reconnect"
│           ├─ User runs /mcp, selects MCPProxy
│           ├─ Check if tools now available
│           │   ├─ YES → Problem solved
│           │   └─ NO → Use debugging-tools:mcpproxy-debug
│           │
│           └─ Never fall back to HTTP API
```

## When to Switch Skills

**Stay in this skill when:**
- MCP tools exist but need to use them
- MCP tools missing and solution is `/mcp` reconnect
- Troubleshooting tool call parameters

**Switch to `debugging-tools:mcpproxy-debug` when:**
- MCPProxy won't start
- Upstream server won't connect
- `/mcp` reconnect doesn't solve the issue
- Need to investigate MCPProxy logs
- Configuration issues

## Quick Checklist

When MCP tools aren't working:

- [ ] Verified `mcp__MCPProxy__*` tools not in tool list
- [ ] Recognized this is MCP connection issue (not "tools don't exist")
- [ ] Told user to run `/mcp` command
- [ ] User selected MCPProxy from list
- [ ] Verified tools now available
- [ ] If still not available, switched to `debugging-tools:mcpproxy-debug`
- [ ] Did NOT fall back to HTTP API
- [ ] Did NOT make multiple curl attempts
- [ ] Did NOT invoke MCP tools as bash commands

If you completed this checklist and tools still aren't available, it's a deeper MCPProxy issue requiring the debugging skill.
