# MCPProxy Skill Improvement Recommendations

**Date:** 2025-11-21
**Based on:** Claude conversation a6858584 analysis

## Executive Summary

The `dev-tools:using-mcpproxy-tools` skill failed to prevent a common failure pattern where the agent tried to use bash commands instead of checking available tools and suggesting `/mcp reconnect`. While the skill documents this pattern well in the "Common Mistakes" section, the core workflow needs to be more explicit about HOW to check for MCP tools.

## Problem Analysis

### What Happened

**User Request:** "check buildkite mcp for something"

**Expected Behavior:**
1. Agent recognizes MCP tool request
2. Agent checks if `mcp__MCPProxy__*` tools are in available tool list
3. Agent sees tools are missing
4. Agent suggests `/mcp reconnect`

**Actual Behavior:**
1. Agent tried to use bash: `claude mcp list`
2. User corrected: "use the mcp search tool to find tools, don't call use bash"
3. Agent listed tools but didn't recognize `mcp__MCPProxy__*` tools were missing
4. Agent said "I don't see any MCP tools available" (correct observation but wrong response)
5. User had to manually run `/mcp reconnect`
6. After reconnect, agent could use MCP tools successfully

### Root Causes

#### 1. Skill Wasn't Triggered
**Problem:** Agent didn't invoke the skill when user mentioned "mcp"

**Why:** Skill description doesn't clearly state trigger patterns like:
- User asks to "check [tool] mcp"
- User asks to "use mcp tools"
- User mentions "buildkite mcp", "slack mcp", etc.

**Impact:** Agent missed opportunity to follow the skill's guidance from the start

**Critical missing pattern:** When user mentions MCPProxy/MCP tools, agent should IMMEDIATELY check if `mcp__MCPProxy__*` tools are available. Missing tools = MCPProxy MCP server not connected = suggest `/mcp reconnect`

#### 2. Unclear "Check Tool List" Step
**Problem:** Skill says "Check if mcp__MCPProxy__* tools are in your tool list" but doesn't explain this is a passive observation

**Current wording:**
```
Are mcp__MCPProxy__* tools in your tool list?
```

**Why unclear:** This could mean:
- Run a command to check
- Call a tool to list tools
- Look at your available tools
- Use bash to query

**Impact:** Agent tried bash command instead of simply observing available tools

#### 3. Missing Visual Example
**Problem:** Skill doesn't show what the tool list looks like when tools are present vs absent

**Why this matters:** Without a concrete example, agents may not recognize:
- What `mcp__MCPProxy__*` tools look like (naming pattern)
- That `mcp__ide__*` tools are different
- That missing `mcp__MCPProxy__*` tools = connection issue

**Impact:** Agent saw `mcp__ide__*` tools and didn't realize `mcp__MCPProxy__*` tools were missing

#### 4. Core Workflow Buried
**Problem:** The critical "don't use bash" guidance is in "Common Mistakes" section, not in the core workflow

**Why this matters:** Agents read core workflow first, may not reach common mistakes

**Impact:** Agent made Mistake #1 (bash commands) despite skill documenting it

## Recommendations

### Priority 1: Add Immediate Detection Pattern at Top

**Add this as the very first thing in the skill (before everything else):**

```markdown
## FIRST: When User Mentions MCPProxy/MCP Tools

**User says anything like:**
- "check buildkite mcp"
- "use mcp tools"
- "call slack mcp"
- Any mention of MCPProxy or MCP tool access

**YOU MUST IMMEDIATELY:**

1. **Look at your available tools** (passive observation - don't run commands)
2. **Scan for `mcp__MCPProxy__*` tools**
   - Example: `mcp__MCPProxy__retrieve_tools`
   - Example: `mcp__MCPProxy__call_tool`

**Decision:**
- ✅ **Found `mcp__MCPProxy__*` tools?** → MCPProxy is connected, use them
- ❌ **Don't see `mcp__MCPProxy__*` tools?** → MCPProxy MCP server not connected

**If tools are missing, IMMEDIATELY tell user:**

> "MCPProxy MCP tools aren't available in this session. The MCPProxy MCP server isn't connected.
>
> Try the `/mcp` command and select MCPProxy to reconnect. Once reconnected, you'll have access to the `mcp__MCPProxy__*` tools."

**DO NOT:**
- Try bash commands
- Try HTTP API with curl
- Try alternative approaches
- Make multiple attempts

**Missing `mcp__MCPProxy__*` tools = Need to reconnect. That's it.**
```

### Priority 2: Make "Check Tool List" Explicit

**Current:**
```markdown
Are mcp__MCPProxy__* tools in your tool list?
```

**Recommended:**
```markdown
## Step 1: Check Your Available Tools (Passive Observation)

**DO NOT run any commands. Just observe.**

Look at the tools available to you in this session. Scan through your tool list.

**What to look for:**
- Tools starting with `mcp__MCPProxy__`
- Examples: `mcp__MCPProxy__retrieve_tools`, `mcp__MCPProxy__call_tool`

**DO NOT:**
- Run bash commands like `claude mcp list`
- Run bash commands like `mcpproxy list-tools`
- Call any tools to "check" - just look at what you already have

**This is a passive check - you're looking at the tools you can already see.**
```

### Priority 3: Add Visual Example

**Add to skill:**
```markdown
## Tool List Examples

**When MCP tools ARE available:**
```
Available tools:
- Bash
- Read
- Write
- mcp__MCPProxy__retrieve_tools  ← Look for these
- mcp__MCPProxy__call_tool       ← Look for these
- mcp__MCPProxy__upstream_servers ← Look for these
- mcp__ide__getDiagnostics
- mcp__ide__executeCode
```

**When MCP tools are NOT available:**
```
Available tools:
- Bash
- Read
- Write
- mcp__ide__getDiagnostics
- mcp__ide__executeCode
← No mcp__MCPProxy__* tools = connection issue
```

**Key distinction:**
- `mcp__ide__*` = Different MCP server (IDE integration)
- `mcp__MCPProxy__*` = MCPProxy tools for accessing upstream servers
- Missing `mcp__MCPProxy__*` = Need to reconnect
```

### Priority 4: Move Critical Warnings to Core Workflow

**Current structure:**
1. Overview
2. Core Decision Tree
3. When to Use
4. Core Pattern
5. ... (later sections)
6. Common Mistakes (Mistake #1: Using bash commands)

**Recommended structure:**
1. Overview
2. **CRITICAL: Do NOT Use Bash Commands** (move from Common Mistakes)
3. Step-by-Step Workflow (with explicit observation guidance)
4. Core Decision Tree
5. When to Use
6. ... (rest)

**Recommended critical warning section:**
```markdown
## CRITICAL: Do NOT Use Bash Commands

**Before you start, understand this:**

MCP tools are NOT bash commands. You check for them by LOOKING at your available tools, not by RUNNING commands.

**DO NOT do this:**
```bash
# ❌ WRONG - These are not bash commands
claude mcp list
mcpproxy list-tools
mcp__MCPProxy__retrieve_tools --query "..."
```

**DO this:**
```
1. Look at your available tool list (the tools in this session)
2. Scan for tools starting with mcp__MCPProxy__*
3. If you see them → Use them
4. If you don't see them → Suggest /mcp reconnect
```

**This is observation, not execution.**
```

### Priority 5: Improve Skill Description for Triggers

**Current description:**
```
Use when MCPProxy is configured and you need to discover or call tools
```

**Recommended description:**
```
Use when MCPProxy is configured and you need to discover or call tools - checks if mcp__MCPProxy__ tools are available, suggests /mcp reconnect if missing, explains when to use MCP tools vs HTTP API for debugging

**Trigger patterns:**
- User asks to "check [service] mcp" (e.g., "check buildkite mcp")
- User asks to "use mcp tools"
- User mentions "[service] mcp tools" (e.g., "slack mcp", "github mcp")
- You need to discover what tools MCPProxy exposes
- You want to call a tool through MCPProxy
- MCPProxy is configured but you're not sure if MCP tools are available
```

### Priority 6: Add "What You're Looking For" Section

**Add after overview:**
```markdown
## What You're Looking For

When you need to use MCPProxy tools, you're looking for tools in your available tool list that match this pattern:

```
mcp__MCPProxy__*
```

**Examples of these tools:**
- `mcp__MCPProxy__retrieve_tools` - Search for tools
- `mcp__MCPProxy__call_tool` - Execute a tool
- `mcp__MCPProxy__upstream_servers` - Manage servers

**How to check:**
1. Look at your available tools in this session
2. Scan for anything starting with `mcp__MCPProxy__`
3. If you find ANY of them → MCP is connected, use them
4. If you find NONE of them → MCP is disconnected, suggest `/mcp reconnect`

**Common confusion:**
- `mcp__ide__*` tools are DIFFERENT (IDE integration, not MCPProxy)
- Only `mcp__MCPProxy__*` tools indicate MCPProxy connection
- Don't run bash commands to check - just look at available tools
```

## Implementation Priority

### High Priority (Core Workflow Fixes)
1. ✅ **Add immediate detection pattern at top** - "When user mentions MCPProxy/MCP, IMMEDIATELY check if tools available"
2. ✅ Make "Check Tool List" step explicit with "passive observation" language
3. ✅ Add visual examples of tool list (with/without MCP tools)
4. ✅ Move "don't use bash" warning to top of skill
5. ✅ Add "What You're Looking For" section

### Medium Priority (Discoverability)
6. ✅ Improve skill description with trigger patterns
7. Add more examples of user queries that should trigger this skill
8. Add checklist at top: "Before you do anything else"

### Low Priority (Nice to Have)
9. Add troubleshooting flowchart diagram
10. Add real conversation examples (success vs failure)
11. Link to this analysis document as a case study

## Testing Recommendations

After implementing improvements, test with scenarios like:

1. **Trigger recognition**: User says "check buildkite mcp for tools"
   - Agent should invoke skill immediately
   - Agent should check tool list (passive observation)
   - Agent should recognize if tools missing

2. **Missing tools**: Agent needs MCP tools but they're not available
   - Agent should NOT use bash commands
   - Agent should immediately suggest `/mcp reconnect`
   - Agent should not fall back to HTTP API

3. **Confusion with other MCP tools**: Only `mcp__ide__*` tools present
   - Agent should recognize `mcp__MCPProxy__*` tools are missing
   - Agent should not say "MCP tools are available" (wrong tools)
   - Agent should suggest `/mcp reconnect`

## Expected Outcomes

After implementing these improvements:

1. **Agents will detect when MCPProxy MCP server isn't connected** - When user mentions MCPProxy/MCP tools, agent immediately checks if `mcp__MCPProxy__*` tools are available
2. **Agents will invoke skill proactively** when user mentions MCP tools
3. **Agents will understand "check tool list" means passive observation** (not running commands)
4. **Agents will recognize missing MCPProxy tools** even when other MCP tools present
5. **Agents will suggest `/mcp reconnect` immediately** when tools are missing, instead of trying bash commands or HTTP API
6. **Skill will prevent the "HTTP API spiral"** documented in troubleshooting guide

## Success Metrics

**Before improvements:** Agent made 3+ attempts with bash/curl before user manually reconnected

**After improvements (target):** Agent suggests `/mcp reconnect` on first attempt, no bash commands

## Related Documents

- Original conversation: `claude-conversation-2025-11-21-a6858584.md` (private conversation log)
- Current skill: `../../skills/using-mcpproxy-tools/SKILL.md`
- Common mistakes: `../../skills/using-mcpproxy-tools/references/common-mistakes.md`
- Troubleshooting: `../../skills/using-mcpproxy-tools/references/troubleshooting-guide.md`

## Conclusion

The skill has excellent content in the "Common Mistakes" section, but the core workflow needs to be more explicit about the first step being a **passive observation** of available tools, not an active command execution. Visual examples and prominent warnings about bash commands should be moved to the top to prevent the failure pattern observed in the conversation.

**Critical missing piece:** The skill needs to start with an immediate detection pattern: **When user mentions MCPProxy/MCP tools, IMMEDIATELY check if `mcp__MCPProxy__*` tools are available. Missing tools = MCPProxy MCP server not connected = suggest `/mcp reconnect`.** This detection pattern should be impossible to miss - it should be the very first thing in the skill.

The skill correctly documents all the patterns, but agents need:
1. **Proactive detection**: Clear trigger to check for MCPProxy connection immediately
2. **Clearer mechanism**: Explicit guidance that checking = passive observation, not command execution
3. **Immediate response**: When tools missing, suggest `/mcp reconnect` right away, no alternatives

With these improvements, agents will catch when the MCPProxy MCP server isn't available and reconnect immediately, rather than trying bash commands or HTTP API workarounds.
