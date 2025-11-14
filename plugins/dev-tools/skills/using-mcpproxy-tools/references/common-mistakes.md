# Common Mistakes - Detailed Examples

**When to use this reference:** You're about to fall back to HTTP API or invoke MCP tools as bash commands.

This reference provides detailed examples of common mistakes when using MCPProxy tools, with explanations of why they're wrong and how to fix them.

## Fundamental Understanding

### What Are MCP Tools?

MCP tools are **functions** exposed by MCP servers. They appear in your tool list with the pattern `mcp__ServerName__tool_name`.

**Key characteristics:**
- Called as functions with object parameters
- Available when MCP connection is established
- Disappear when MCP connection is lost
- NOT bash commands

### What Is the HTTP API?

The HTTP API is MCPProxy's **debugging interface**. It provides direct HTTP access to MCPProxy's internals.

**Key characteristics:**
- Accessed via `curl http://localhost:8080/...`
- Requires API key authentication
- Used for debugging MCPProxy itself
- NOT the primary way to use MCPProxy from Claude Code

### When to Use Each

| Scenario | Use MCP Tools | Use HTTP API |
|----------|--------------|--------------|
| Discovering available tools | ✅ Yes | ❌ No |
| Calling a tool through MCPProxy | ✅ Yes | ❌ No |
| Debugging why MCPProxy won't start | ❌ No | ✅ Yes |
| Checking server connection status | ❌ No | ✅ Yes |
| Investigating configuration issues | ❌ No | ✅ Yes |
| Normal tool usage in Claude Code | ✅ Yes | ❌ No |

**From Claude Code's perspective:** Use MCP tools. HTTP API is for the `mcpproxy-debug` skill.

## Mistake 1: Invoking MCP Tools as Bash Commands

### ❌ Wrong: Using Bash Tool

```bash
# Agent tries to run as bash command
mcp__MCPProxy__retrieve_tools --query "slack tools"

# Or with different syntax
mcp__MCPProxy__call_tool --name slack:post_message --args '{"channel": "#general"}'

# Or trying to find it in PATH
which mcp__MCPProxy__retrieve_tools

# Or checking if it exists
command -v mcp__MCPProxy__retrieve_tools
```

**Why this is wrong:**
- `mcp__MCPProxy__*` are MCP tools (functions), not bash commands
- They don't exist in your PATH
- They're not executables you can run
- They're capabilities provided by an MCP server

**What happens:**
```
bash: mcp__MCPProxy__retrieve_tools: command not found
```

### ✅ Correct: Call as MCP Tool

```typescript
// Call as a function with object parameter
mcp__MCPProxy__retrieve_tools({
  query: "slack tools",
  limit: 10
})

// Another example
mcp__MCPProxy__call_tool({
  name: "slack:post_message",
  args_json: JSON.stringify({
    channel: "#general",
    message: "Hello"
  })
})
```

**Why this is correct:**
- Calls the MCP tool as a function
- Passes parameters as an object
- Uses the MCP protocol (not bash)

### How to Tell the Difference

**MCP tools:**
- Pattern: `mcp__ServerName__tool_name`
- Examples: `mcp__MCPProxy__retrieve_tools`, `mcp__ide__getDiagnostics`
- Call as: Function with object parameter
- Via: MCP tool invocation

**Bash commands:**
- Pattern: Regular command names
- Examples: `mcpproxy`, `docker`, `curl`, `grep`
- Call as: Bash command with flags/arguments
- Via: Bash tool

**Simple rule:** If it starts with `mcp__`, it's an MCP tool (function), not a bash command.

## Mistake 2: Falling Back to HTTP API

### ❌ Wrong: Using curl Instead of MCP Tools

```bash
# Agent tries MCP tool
mcp__MCPProxy__retrieve_tools({query: "slack tools"})

# Gets error
Error: "No such tool available: mcp__MCPProxy__retrieve_tools"

# Agent falls back to HTTP API
curl -H "X-API-Key: $(grep api_key ~/.mcpproxy/mcp_config.json | cut -d'"' -f4)" \
  "http://127.0.0.1:8080/api/v1/tools" | python3 -m json.tool

# Or tries different variations
curl "http://127.0.0.1:8080/api/v1/tools?apikey=..."
curl -s "http://127.0.0.1:8080/api/v1/servers" | python3 -c "import sys, json; ..."
```

**Why this is wrong:**
- HTTP API is for debugging MCPProxy, not for using it
- The error means MCP connection is lost, not that tools don't exist
- curl doesn't solve the connection problem
- You're working around the issue instead of fixing it

**What's really happening:**
- MCPProxy is running, but MCP connection to Claude Code is broken
- MCP tools exist but aren't available in this session
- Need to reconnect MCP, not bypass it with HTTP

### ✅ Correct: Recognize Connection Issue

```typescript
// Agent tries MCP tool
mcp__MCPProxy__retrieve_tools({query: "slack tools"})

// Gets error
Error: "No such tool available: mcp__MCPProxy__retrieve_tools"

// Agent recognizes the issue
// This is an MCP connection problem, not a "tools don't exist" problem

// Agent tells user
"MCPProxy MCP tools aren't available in this session.
Try the `/mcp` command and select MCPProxy to reconnect.
Once reconnected, you'll have access to mcp__MCPProxy__retrieve_tools."
```

**Why this is correct:**
- Recognizes the real problem (MCP connection)
- Provides the correct solution (/mcp reconnect)
- Doesn't bypass MCP with HTTP API
- Addresses root cause, not symptoms

## Mistake 3: The HTTP API Spiral

### ❌ Wrong: Multiple curl Attempts

This is a real example from a conversation where the agent made **5 attempts** with HTTP API:

```bash
# Attempt 1: Basic curl
curl "http://127.0.0.1:8080/api/v1/tools?apikey=KEY"

# Attempt 2: With json.tool
curl "http://127.0.0.1:8080/api/v1/tools?apikey=KEY" | python3 -m json.tool

# Attempt 3: With grep
curl "http://127.0.0.1:8080/api/v1/tools?apikey=KEY" | grep "redash"

# Attempt 4: Different parsing
curl "http://127.0.0.1:8080/api/v1/tools?apikey=KEY" | python3 -c "import json; ..."

# Attempt 5: Python script
python3 << EOF
import requests
response = requests.get("http://127.0.0.1:8080/api/v1/tools?apikey=KEY")
...
EOF
```

**Why this is wrong:**
- Making multiple HTTP attempts means you're stuck in the wrong approach
- Each attempt is trying different parsing, not addressing the real issue
- The real issue is MCP connection, not parsing
- You've spent 5 attempts working around instead of fixing

**Signs you're in the HTTP API spiral:**
- Multiple curl attempts with different parsing strategies
- Trying Python/jq/grep to parse HTTP responses
- Each attempt uses a different technique but same API
- Thinking "maybe this parsing approach will work"

### ✅ Correct: Stop After First Failure

```typescript
// Agent tries MCP tool
mcp__MCPProxy__call_tool({...})

// Gets error
Error: "No such tool available: mcp__MCPProxy__call_tool"

// Agent STOPS and recognizes
// This is an MCP connection issue

// Agent tells user immediately (no HTTP attempts)
"MCPProxy MCP tools aren't available. The MCP connection isn't established.
Try the `/mcp` command and select MCPProxy to reconnect."
```

**Why this is correct:**
- Stops immediately after recognizing the issue
- Doesn't make multiple curl attempts
- Identifies root cause (MCP connection)
- Provides correct solution (/mcp reconnect)

**Rule:** If you're making a second curl attempt with different parsing, you're in the spiral. Stop and suggest `/mcp` instead.

## Mistake 4: Assuming Tools Don't Exist

### ❌ Wrong: Concluding Tools Are Missing

```typescript
// Agent tries
mcp__MCPProxy__retrieve_tools({query: "..."})

// Gets error
Error: "No such tool available: mcp__MCPProxy__retrieve_tools"

// Agent concludes
"The mcp__MCPProxy__retrieve_tools tool doesn't exist.
The glean tools are accessed through the MCPProxy API instead."

// Falls back to HTTP API
curl "http://127.0.0.1:8080/api/v1/tools?apikey=..."
```

**Why this is wrong:**
- The tool DOES exist when MCP is connected
- The error means connection issue, not "tool doesn't exist"
- Wrong diagnosis leads to wrong solution
- HTTP API doesn't solve the connection problem

**What's really happening:**
- MCPProxy is configured as an MCP server
- The `mcp__MCPProxy__*` tools exist in that configuration
- They're just not available in this session
- Need to reconnect, not conclude they don't exist

### ✅ Correct: Recognize Connection Issue

```typescript
// Agent tries
mcp__MCPProxy__retrieve_tools({query: "..."})

// Gets error
Error: "No such tool available"

// Agent recognizes correctly
"MCPProxy MCP tools should exist but aren't available.
This means the MCP server isn't connected."

// Agent suggests fix
"Use the `/mcp` command to reconnect to MCPProxy.
Once connected, you'll have access to mcp__MCPProxy__retrieve_tools."
```

**Why this is correct:**
- Understands tools exist but aren't available
- Identifies the real issue (not connected)
- Provides correct solution (/mcp reconnect)

**Mental model:** "No such tool available" ≠ "Tool doesn't exist". It means "Tool exists but isn't available in this session."

## Mistake 5: Wrong Rationalization

### ❌ Wrong: Rationalizing HTTP API Usage

Common rationalizations agents use to justify HTTP API:

```
"The MCP tools aren't available, so I'll use the HTTP API"
→ Wrong: Should suggest /mcp reconnect instead

"HTTP API is more direct"
→ Wrong: MCP tools are the primary interface in Claude Code

"I can get the same information via HTTP"
→ Wrong: HTTP API is for debugging, not normal usage

"Let me check MCPProxy is running via curl"
→ Wrong: Running ≠ Connected. Use /mcp to connect.

"The API key is easy to get from config"
→ Wrong: Having API key doesn't mean you should use HTTP API

"curl is simpler than MCP tools"
→ Wrong: Simpler ≠ Correct. Use MCP tools in Claude Code.
```

**Why these are wrong:**
- They rationalize working around the problem
- They avoid the real fix (/mcp reconnect)
- They treat symptoms instead of root cause
- They use debugging interface for normal usage

### ✅ Correct: Stop and Reconnect

```typescript
// Agent tries MCP tool
mcp__MCPProxy__retrieve_tools({...})

// Gets error
Error: "No such tool available"

// Agent doesn't rationalize
// No "let me try HTTP instead"
// No "HTTP is simpler"
// Just recognize and suggest fix

"MCPProxy MCP tools aren't available.
Try `/mcp` command to reconnect."
```

**Why this is correct:**
- No rationalization for wrong approach
- Addresses root cause immediately
- Suggests correct solution
- Doesn't work around the problem

## Mistake 6: Confusing "Running" with "Connected"

### ❌ Wrong: Checking if Process Is Running

```bash
# Agent checks if mcpproxy process is running
ps aux | grep mcpproxy

# Sees process running
josh.nichols 12345 ... mcpproxy

# Agent concludes
"MCPProxy is running, so the tools should work.
Let me try the HTTP API to access it."

curl "http://127.0.0.1:8080/api/v1/tools?apikey=..."
```

**Why this is wrong:**
- Running ≠ Connected
- Process can run but MCP not connected to Claude Code
- HTTP API access doesn't mean MCP tools are available
- Checking process doesn't solve connection issue

**What's really happening:**
- MCPProxy process is running (server is up)
- HTTP API is accessible (server is healthy)
- BUT: MCP connection to Claude Code is not established
- MCP tools won't be available until `/mcp` reconnects

### ✅ Correct: Check Tool Availability Directly

```typescript
// Don't check if process is running
// Just check if MCP tools are available

// Are mcp__MCPProxy__* tools in tool list?
// NO

// Then suggest reconnect
"MCPProxy MCP tools aren't available in this session.
Try `/mcp` command to reconnect."
```

**Why this is correct:**
- Checks actual availability, not process status
- Recognizes that running ≠ connected
- Provides correct solution (/mcp reconnect)

**Mental model:**
- Process running = HTTP API works (debugging tools)
- MCP connected = MCP tools work (normal usage)
- These are independent states

## Quick Decision Tree

Use this to avoid mistakes:

```
Need to use MCPProxy tools?
│
├─ Check: Are mcp__MCPProxy__* in tool list?
│  │
│  ├─ YES → Use MCP tools
│  │        (mcp__MCPProxy__retrieve_tools, call_tool, etc.)
│  │
│  └─ NO → Do NOT fall back to HTTP API
│           Tell user: "Try /mcp command to reconnect"
│
└─ Never:
    - Use curl
    - Invoke MCP tools as bash commands
    - Make multiple HTTP attempts
    - Rationalize HTTP API usage
    - Check if process is running
```

## Summary: How to Avoid These Mistakes

**Do:**
1. Check if `mcp__MCPProxy__*` tools are in your tool list
2. If yes → Use them (as functions with object parameters)
3. If no → Suggest `/mcp` reconnect
4. Stop immediately when tools aren't available

**Don't:**
1. Invoke MCP tools as bash commands
2. Fall back to HTTP API for normal usage
3. Make multiple curl attempts
4. Rationalize working around the connection issue
5. Confuse "running" with "connected"

**Remember:** MCP tools are the primary interface. HTTP API is for debugging MCPProxy, not for using it.
