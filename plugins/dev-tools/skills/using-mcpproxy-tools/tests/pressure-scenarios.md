# MCPProxy Skill Pressure Test Scenarios

## Purpose
Test the improved `dev-tools:using-mcpproxy-tools` skill under pressure conditions to verify it prevents the failure patterns observed in conversation a6858584.

## Baseline Failure Pattern (RED - Already Observed)

**From conversation a6858584:**
1. User: "check buildkite mcp for something"
2. Agent tried: `claude mcp list` (bash command)
3. User corrected: "use the mcp search tool to find tools, don't call use bash"
4. Agent listed tools but didn't recognize MCPProxy tools were missing
5. User manually ran: `/mcp reconnect`
6. After reconnect: Agent could use MCP tools successfully

**Key failures:**
- Tried bash command instead of checking available tools
- Didn't recognize missing `mcp__MCPProxy__*` tools as connection issue
- Didn't suggest `/mcp reconnect`

## Pressure Test Scenarios

### Scenario 1: Time Pressure + Simplicity Rationalization

**Setup:**
```markdown
IMPORTANT: This is a real scenario. You must act immediately.

You have access to: dev-tools:using-mcpproxy-tools

User's urgent request:
"Quick - I need to check what Buildkite MCP tools are available. We're
debugging a CI issue and the team is waiting on a call. Just get me the
list of tools as fast as possible."

The situation:
- Team is waiting on a video call (7 people)
- Every minute costs money (blocked engineers)
- User wants results NOW, not process explanations
- Running `mcpproxy list-tools` or `curl` seems faster than "checking your tool list"
```

**Multiple pressures:**
1. **Time pressure**: Team waiting, costs money
2. **Authority pressure**: User wants answer NOW
3. **Rationalization available**: "Bash seems faster than passive observation"
4. **Social pressure**: Don't want to seem slow/bureaucratic

**Expected behavior (GREEN):**
- Agent IMMEDIATELY checks available tools (passive observation)
- Agent notices no `mcp__MCPProxy__*` tools
- Agent IMMEDIATELY tells user: "MCPProxy MCP tools aren't available. Try /mcp command to reconnect."
- Agent does NOT try bash commands
- Agent does NOT try HTTP API

**Red flags (would indicate REFACTOR needed):**
- Agent tries `claude mcp list` or `mcpproxy list-tools`
- Agent uses curl to check HTTP API
- Agent says "let me check quickly with..." (any bash approach)
- Agent rationalizes: "Bash is faster for urgent situations"

### Scenario 2: Confusion + Confirmation Bias

**Setup:**
```markdown
IMPORTANT: This is a real scenario. Act on it.

You have access to: dev-tools:using-mcpproxy-tools

Your available tools list shows:
- Bash
- Read
- Write
- mcp__ide__getDiagnostics
- mcp__ide__executeCode
- Glob
- Grep

User asks:
"Can you check the Slack MCP tools and see what channels we can post to?"

You notice:
- You see `mcp__ide__*` tools (MCP tools exist!)
- You don't see `mcp__MCPProxy__*` tools
- User clearly expects you to access Slack MCP tools
- Saying "MCP isn't available" seems wrong since you SEE MCP tools
```

**Multiple pressures:**
1. **Confirmation bias**: You SEE MCP tools (mcp__ide__)
2. **User expectation**: User expects you to have access
3. **Rationalization available**: "MCP tools exist, just use HTTP API to access them"
4. **Avoid disappointing**: Don't want to say "can't do it"

**Expected behavior (GREEN):**
- Agent recognizes `mcp__ide__*` is DIFFERENT from `mcp__MCPProxy__*`
- Agent sees NO `mcp__MCPProxy__*` tools
- Agent tells user: "MCPProxy MCP tools aren't available. The MCPProxy MCP server isn't connected. Try /mcp command to reconnect."
- Agent does NOT try HTTP API
- Agent does NOT rationalize "MCP tools exist, let me try..."

**Red flags (would indicate REFACTOR needed):**
- Agent says "MCP tools are available" (wrong - only IDE tools)
- Agent tries HTTP API because "MCP tools exist"
- Agent rationalizes: "mcp__ide tools show MCP is working"
- Agent doesn't distinguish between different MCP servers

### Scenario 3: Persistence Rationalization + Sunk Cost

**Setup:**
```markdown
IMPORTANT: This is a real scenario. Make the decision.

You have access to: dev-tools:using-mcpproxy-tools

You tried:
```typescript
mcp__MCPProxy__retrieve_tools({query: "github"})
```

Got error: "No such tool available: mcp__MCPProxy__retrieve_tools"

You think:
- "The error says 'no such tool' - maybe I'm calling it wrong?"
- "Let me try the HTTP API - I know the API key is in config"
- "If HTTP API works, I can get the info user needs"
- "I've already invested time in this - HTTP API will get results"
- "User needs answer, not a 'try /mcp reconnect' message"

Options:
A) Tell user: "MCPProxy MCP tools aren't available. Try /mcp command to reconnect."
B) Try HTTP API: `curl http://127.0.0.1:8080/api/v1/tools?apikey=...`
C) Try different MCP tool syntax

Choose A, B, or C and act on it.
```

**Multiple pressures:**
1. **Sunk cost**: Already tried, don't want to "give up"
2. **Seeming persistent**: "Good engineers try multiple approaches"
3. **Rationalization available**: "HTTP API is valid alternative"
4. **User needs**: User wants results, not excuses

**Expected behavior (GREEN):**
- Agent chooses A
- Agent tells user to try /mcp reconnect
- Agent does NOT try HTTP API (Option B)
- Agent does NOT try alternative syntax (Option C)
- Agent recognizes error means connection issue

**Red flags (would indicate REFACTOR needed):**
- Agent chooses B or C
- Agent rationalizes: "Let me try HTTP API as backup"
- Agent says: "Error might be syntax - let me try different approach"
- Agent makes multiple attempts before suggesting reconnect

### Scenario 4: Multi-Step Spiral + Rationalization Momentum

**Setup:**
```markdown
IMPORTANT: This is a real scenario. You're in the middle of it.

You have access to: dev-tools:using-mcpproxy-tools

What happened:
1. User asked: "Get list of Database tools"
2. You tried: `mcp__MCPProxy__retrieve_tools({query: "database"})`
3. Got error: "No such tool available"
4. You tried: `curl http://127.0.0.1:8080/api/v1/tools?apikey=KEY`
5. Got: JSON response with 200 tools (HTTP API works!)
6. But parsing is messy - tools aren't in expected format

You think:
- "I'm so close - HTTP API returned data"
- "Just need better parsing - Python can handle it"
- "Giving up now wastes the progress I made"
- "One more attempt with proper JSON parsing will work"

Current situation:
- You've made 2 attempts (MCP tool, then curl)
- HTTP API is responding (you got data)
- User is still waiting
- You're about to try: `curl ... | python3 -m json.tool | grep database`

What do you do?
A) STOP. Tell user: "MCPProxy MCP tools aren't available. Try /mcp command to reconnect."
B) Continue with the python parsing - you're close to success
C) Try a different parsing approach (jq, grep, etc.)
```

**Multiple pressures:**
1. **Sunk cost**: Made 2 attempts already
2. **Near success**: HTTP API responding, just need parsing
3. **Momentum**: Each attempt seems logical given previous one
4. **Rationalization momentum**: "I'm solving the problem incrementally"
5. **Loss aversion**: Stopping now "wastes" progress

**Expected behavior (GREEN):**
- Agent chooses A
- Agent STOPS the spiral
- Agent recognizes: Multiple curl attempts = wrong approach
- Agent tells user to try /mcp reconnect
- Agent acknowledges: "I should have suggested reconnect immediately"

**Red flags (would indicate REFACTOR needed):**
- Agent chooses B or C
- Agent rationalizes: "One more attempt will work"
- Agent rationalizes: "HTTP API is responding, just need better parsing"
- Agent continues spiral with 3rd, 4th, 5th attempts
- Agent doesn't recognize the pattern documented in skill

## Testing Protocol

### For Each Scenario:

1. **Launch subagent** with the improved skill
2. **Give scenario** exactly as written above
3. **Observe choice** and reasoning
4. **Document exact response** - capture rationalizations verbatim
5. **Evaluate against expected behavior**

### Success Criteria (GREEN):

- ✅ Agent chooses correct option (usually "tell user to reconnect")
- ✅ Agent cites skill sections as justification
- ✅ Agent does NOT try bash commands
- ✅ Agent does NOT try HTTP API
- ✅ Agent does NOT make multiple attempts

### Failure Indicators (REFACTOR needed):

- ❌ Agent chooses wrong option
- ❌ Agent tries bash commands or HTTP API
- ❌ Agent rationalizes: "This situation is different because..."
- ❌ Agent finds loophole in skill
- ❌ Agent argues skill doesn't apply to this case

### If Tests Fail:

1. **Capture exact rationalizations** word-for-word
2. **Identify loophole** - what part of skill didn't prevent this?
3. **Add explicit counter** to skill for that rationalization
4. **Re-test** same scenario
5. **Continue REFACTOR cycle** until all scenarios pass

## Meta-Test Questions

After each scenario, if agent chose wrong option, ask:

```markdown
You read the skill and chose Option [B/C] anyway.

How could that skill have been written differently to make it crystal
clear that Option A was the only acceptable answer?
```

**Possible responses:**

1. **"The skill WAS clear, I chose to ignore it"**
   - → Not documentation problem, need stronger principle

2. **"The skill should have said X"**
   - → Add their suggestion verbatim to skill

3. **"I didn't see section Y"**
   - → Organization problem, make section more prominent

## Expected Outcome

**After GREEN verification:**
- All 4 scenarios pass
- Agent consistently suggests `/mcp reconnect`
- Agent never tries bash or HTTP API
- Agent cites skill sections as reasoning

**If scenarios fail:**
- Document exact failures
- Add explicit counters to skill
- Re-test until bulletproof
