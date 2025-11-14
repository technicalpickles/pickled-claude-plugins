# Using MCPProxy Tools Skill

## Overview

This skill teaches Claude agents how to properly use MCPProxy MCP tools instead of falling back to HTTP API or CLI commands when MCP tools should be available.

## Problem Statement

When MCPProxy is configured as an MCP server in Claude Code, it exposes tools with the naming pattern `mcp__MCPProxy__*`. However, agents frequently:

1. Try to invoke these as bash commands
2. Get "tool not available" errors and immediately fall back to HTTP API
3. Get stuck in loops trying different HTTP API parsing strategies
4. Rationalize that "the tool doesn't exist" instead of recognizing connection issues

This results in wasted effort, user frustration, and incorrect approaches.

## What This Skill Teaches

### Core Concepts

1. **Tool Availability Check**: How to verify if `mcp__MCPProxy__*` tools are in the tool list
2. **Proper Invocation**: MCP tools are functions, not bash commands
3. **Error Interpretation**: "No such tool available" = MCP connection issue, not "tool doesn't exist"
4. **Reconnection Guidance**: Suggest `/mcp` command when tools are missing
5. **Context Differentiation**: When to use MCP tools vs when to use HTTP API (debugging MCPProxy itself)

### Key Patterns

**Check First:**
```typescript
// Look for these tools in your tool list:
mcp__MCPProxy__retrieve_tools
mcp__MCPProxy__call_tool
mcp__MCPProxy__upstream_servers
// ... etc
```

**If Available, Use Them:**
```typescript
mcp__MCPProxy__retrieve_tools({
  query: "slack post message"
})
```

**If Missing, Suggest Reconnection:**
```
"MCPProxy MCP tools aren't available. Try the /mcp command
and select MCPProxy to reconnect."
```

**Never Fall Back to HTTP API:**
```bash
# DON'T DO THIS when MCP tools should exist:
curl http://127.0.0.1:8080/api/v1/tools?apikey=...
```

## Failure Modes Addressed

This skill was developed using TDD (Test-Driven Development) based on actual failure cases observed in real conversations.

### 1. Bash Invocation (Observed)

**Symptom:** Agent tries to run MCP tool as bash command

**Example:**
```bash
# WRONG
mcp__MCPProxy__retrieve_tools --query "slack tools"
```

**Solution:** Skill explicitly shows function invocation syntax vs bash commands

### 2. HTTP API Fallback (Conversation: c235ae43...jsonl, Line 12-14)

**Symptom:** Agent gets "tool not available" and immediately switches to curl

**Example from actual conversation:**
```
Try: mcp__MCPProxy__call_tool(...)
Error: "No such tool available"
Response: "Let me check what Redash tools are available:"
→ curl http://127.0.0.1:8080/api/v1/servers/redash/tools?apikey=...
```

**Solution:** Skill teaches to recognize connection issue and suggest `/mcp` reconnect

### 3. HTTP API Spiral (Conversation: c235ae43...jsonl, Lines 14-26)

**Symptom:** Agent makes multiple curl attempts with different parsing strategies

**Example from actual conversation (5 attempts before user interrupted):**
1. `curl ... | python3 -m json.tool`
2. `curl ... | python3 -c "import json; parse..."`
3. `curl ... | python3 -m json.tool | grep`
4. `curl ... | grep` (without json.tool)
5. Python script wrapping curl with custom parsing

**Solution:** Skill explicitly warns against "HTTP API spiral" and teaches to stop after first failure

### 4. Wrong Rationalization (Warmup transcript: 2025-11-13_23-56-10Z)

**Symptom:** Agent concludes "tool doesn't exist" instead of "MCP not connected"

**Example from actual conversation:**
```
Try: mcp__MCPProxy__retrieve_tools
Error: "No such tool available"
Rationalization: "The mcp__MCPProxy__retrieve_tools tool doesn't
exist - the glean tools are accessed through the MCPProxy API"
```

**Solution:** Skill corrects this rationalization and explains the real issue

## Development Process (TDD)

### RED Phase - Baseline Testing

**Test 1: Natural Behavior (No Tools Loaded)**
- Agent tried CLI commands (`mcpproxy search-servers`, `mcpproxy call tool`)
- Rationalization: "CLI is the standard way to interact with MCP servers"
- Result: Failed due to CLI limitations

**Test 2: Pressure Test (Tools Loaded)**
- Agent correctly used MCP tools even under time pressure
- Result: Passed (agents naturally use MCP tools when available)

**Key Finding:** The problem isn't using MCP tools when available - it's recognizing when they're missing and responding appropriately.

### GREEN Phase - Skill Development

Created skill addressing specific failure patterns:
- Bash invocation prevention
- Connection issue recognition
- HTTP API fallback prevention
- Spiral pattern warning

### REFACTOR Phase - Real Conversation Analysis

Analyzed actual failure conversation (c235ae43-9941-4910-b498-63c48545da1a.jsonl):
- Added "HTTP API spiral" warning
- Updated examples with real conversation snippets
- Added red flags for all observed patterns

## Skill Structure

### Sections

1. **Overview** - What MCPProxy tools are and when to use them
2. **When to Use** - Triggering conditions and differentiation from mcpproxy-debug
3. **Quick Reference** - Table of MCP tools vs CLI commands
4. **Step-by-Step Guide** - Tool availability check and proper usage
5. **Core Pattern** - Discover → Examine → Call workflow
6. **Common Mistakes** - Before/after examples of all failure modes
7. **Troubleshooting** - What to do when tools are missing
8. **Red Flags** - Thoughts that indicate you're about to fail
9. **Real-World Examples** - Actual conversation failures with corrections
10. **Summary** - Quick checklist

## Testing Results

### Before Skill

- ❌ Falls back to HTTP API when MCP tools missing
- ❌ Makes multiple curl attempts with different parsing
- ❌ Rationalizes "tool doesn't exist"
- ❌ Never suggests `/mcp` reconnection

### After Skill

- ✅ Recognizes tool availability issues
- ✅ Suggests `/mcp` reconnect when appropriate
- ✅ Understands MCP tools vs HTTP API contexts
- ✅ Avoids HTTP API spiral

## Usage

### For Agents

This skill is automatically loaded when:
- You encounter MCPProxy in the environment
- You get errors about `mcp__MCPProxy__*` tools
- You're working with MCP server tools

### For Developers

**When to update this skill:**
1. New failure patterns are observed
2. MCPProxy MCP tool naming changes
3. Reconnection workflow changes
4. New confusion patterns emerge

**Testing approach:**
1. Create scenario where MCPProxy tools are NOT loaded
2. Give agent a task requiring MCPProxy
3. Verify agent suggests `/mcp` reconnect instead of HTTP API

## Related Skills

- **debugging-tools:mcpproxy-debug** - For debugging MCPProxy itself (connection failures, Docker isolation, config issues)
- **superpowers-developing-for-claude-code:working-with-claude-code** - Official Claude Code documentation including MCP concepts

## File Structure

```
using-mcpproxy-tools/
├── SKILL.md                      # Main skill reference
├── README.md                     # This file
└── [test artifacts in .scratch/]
    ├── baseline-test.md          # Original test scenario
    ├── baseline-results.md       # Results without skill
    ├── actual-failure-case.md    # Warmup transcript analysis
    ├── curl-fallback-failure.md  # JSONL conversation analysis
    ├── bash-invocation-failure.md # Bash command issue
    ├── mcp-tools-baseline-test.md # Test design
    └── mcp-tools-findings.md     # Investigation findings
```

## Key Metrics

**Lines of skill:** ~300 (concise, focused on specific failures)
**Real conversations analyzed:** 2
**Failure modes addressed:** 4
**Development approach:** TDD with real failure cases
**Test iterations:** 3 (baseline, pressure, with-skill)

## Success Criteria

An agent using this skill should:
1. ✅ Check tool list for `mcp__MCPProxy__*` before attempting alternatives
2. ✅ Invoke MCP tools as functions, not bash commands
3. ✅ Recognize "No such tool available" as connection issue
4. ✅ Suggest `/mcp` reconnect when tools are missing
5. ✅ Never fall back to HTTP API when MCP tools should exist
6. ✅ Stop after first connection error (no HTTP API spiral)

## Contributing

When adding new failure patterns:
1. Document the actual conversation where failure occurred
2. Extract exact error messages and agent responses
3. Add to "Common Mistakes" or "Red Flags" sections
4. Create test scenario to verify fix
5. Update this README with new pattern

## License

Part of pickled-claude-plugins repository.
