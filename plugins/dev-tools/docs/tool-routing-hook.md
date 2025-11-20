# Tool Routing Hook - Design Principles

## Intent

The Tool Routing Hook intercepts tool calls before execution to suggest better alternatives for specific services. It prevents Claude from using WebFetch when more appropriate tools exist (MCP servers, CLI tools, etc.).

**Core problem:** Claude may attempt to use WebFetch for services that:
- Require authentication WebFetch can't provide
- Have better-structured alternatives (MCP servers, CLI tools)
- Return HTML that requires scraping when structured APIs exist

**Solution:** Block WebFetch at the hook level and provide actionable guidance toward better tools.

## Design Principles

### 1. Fail Open, Not Closed

The hook **never breaks Claude's functionality** due to configuration errors.

**Implementation:**
- Invalid JSON config → Allow WebFetch
- Missing config file → Allow WebFetch
- Regex compilation error → Allow WebFetch
- Unexpected exceptions → Allow WebFetch

**Why:** It's better to let an occasional WebFetch through than to block legitimate requests or crash Claude. The hook is an optimization, not a security boundary.

### 2. Token Efficiency by Default

Token usage adds up quickly when hooks block tools frequently.

**Normal mode (default):**
```
Use `gh pr view <number>` for GitHub PRs.

This works for both public and private PRs and provides better formatting than HTML scraping.
```

**Debug mode (`TOOL_ROUTING_DEBUG=1`):**
```
❌ Tool Routing: github-pr
Matched URL: https://github.com/user/repo/pull/42
Pattern: github\.com/[^/]+/[^/]+/pull/\d+

Use `gh pr view <number>` for GitHub PRs.

This works for both public and private PRs and provides better formatting than HTML scraping.
```

**Rationale:**
- Normal users see only the helpful message (saves ~40 tokens per block)
- URL is redundant (Claude already knows what URL it tried)
- Route name and pattern are debugging info, not user guidance
- Debug mode preserves full diagnostic output when needed

### 3. Actionable Messages

Blocked tool messages must tell Claude **exactly what to do instead**.

**Bad:**
```
Atlassian URLs not supported. Use MCP tools.
```

**Good:**
```
Use Atlassian MCP tools for Jira/Confluence.

Call: mcp__MCPProxy__retrieve_tools
Query: 'jira confluence atlassian issue'

MCP tools provide authentication and structured data.
```

**Why good messages work:**
- Specific tool call with exact parameters
- Explains the benefit (authentication, structured data)
- Claude can execute immediately without additional research

### 4. Declarative Configuration

Route patterns and messages live in `tool-routes.json`, not Python code.

**Benefits:**
- Users can add services without touching Python
- Changes don't require code review
- Regex patterns are visible and testable
- Messages can be iterated quickly

**Format:**
```json
{
  "routes": {
    "service-name": {
      "pattern": "regex-pattern",
      "message": "Actionable guidance with specific tool calls"
    }
  }
}
```

### 5. Comprehensive Testing

The hook includes a test suite (`test_tool_routing.py`) covering:

**Functional tests:**
- Configured URLs are blocked
- Non-matching URLs pass through
- Non-WebFetch tools are ignored
- Empty/malformed input fails open

**Mode-specific tests:**
- Normal mode excludes debug output
- Debug mode includes full diagnostics
- Both modes block correctly

**Why testing matters:**
- Hooks run on every tool call; failures affect all operations
- Silent failures are hard to debug
- Tests prevent regressions as routes are added

### 6. Progressive Disclosure

Debug output is hidden by default but available when needed.

**Three levels:**
1. **Normal operation:** Just the helpful message
2. **Debug mode:** Full diagnostics (route, URL, pattern)
3. **Stderr debug logs:** Granular execution flow (config loading, pattern matching)

**When to use debug mode:**
- Adding new routes and testing patterns
- Investigating why a URL matched/didn't match
- Debugging hook behavior in production

**Activation:**
```bash
export TOOL_ROUTING_DEBUG=1
```

## Implementation Details

### Hook Flow

```
1. Load config from hooks/tool-routes.json
   └─> If error: Allow WebFetch (fail open)

2. Extract tool_name from stdin
   └─> If not WebFetch: Allow (optimization)

3. Extract URL from tool_input
   └─> If no URL: Allow

4. Check URL against each route pattern
   └─> If match found: Block with message
   └─> If no match: Allow

5. Exit code determines behavior
   └─> 0: Allow tool execution
   └─> 1: Block tool execution (show stderr)
```

### Pattern Matching

Patterns use Python's `re.search()` with case-insensitive matching.

**Key considerations:**
- Patterns are **substrings**, not full matches (use anchors if needed)
- Use `\\.` to match literal dots
- Escape special regex characters (`[](){}+*?|^$`)
- Test patterns against various URL formats

**Examples:**

Match any Atlassian subdomain:
```json
"pattern": "https?://[^/]*\\.atlassian\\.net"
```

Match GitHub PR URLs:
```json
"pattern": "github\\.com/[^/]+/[^/]+/pull/\\d+"
```

### Configuration Location

Config must be at: `$CLAUDE_PLUGIN_ROOT/hooks/tool-routes.json`

The hook uses `CLAUDE_PLUGIN_ROOT` to find its config relative to the plugin directory, allowing operation from any location without hardcoded paths.

## Adding New Routes

### Process

1. Identify the URL pattern to match
2. Determine the better alternative (MCP server, CLI tool, etc.)
3. Add route to `hooks/tool-routes.json`
4. Add test case to `hooks/test_tool_routing.py`
5. Run test suite to verify

### Example: Adding Linear Support

**1. Identify pattern:**
- Linear issue URLs: `https://linear.app/team/issue/PROJ-123`
- Pattern: `linear\\.app/[^/]+/issue`

**2. Determine alternative:**
- Use Linear MCP server via MCPProxy

**3. Add route:**
```json
{
  "routes": {
    "linear": {
      "pattern": "linear\\.app/[^/]+/issue",
      "message": "Use Linear MCP tools for issue access.\n\nCall: mcp__MCPProxy__retrieve_tools\nQuery: 'linear issue project'\n\nMCP tools provide authentication and structured data."
    }
  }
}
```

**4. Add test:**
```python
test(
    "Linear issue URL blocks",
    {
        "tool_name": "WebFetch",
        "tool_input": {"url": "https://linear.app/myteam/issue/PROJ-123"}
    },
    expected_exit=1,
    should_contain="Linear MCP tools"
)
```

**5. Verify:**
```bash
python3 hooks/test_tool_routing.py
```

## Future Considerations

### Potential Enhancements

1. **Allow-list patterns:** Routes that explicitly allow certain WebFetch URLs
2. **Rate limiting:** Warning after N blocks to prevent hook fatigue
3. **Analytics:** Track which routes block most frequently
4. **Dynamic patterns:** Load patterns from external sources
5. **Parameter extraction:** Suggest commands with extracted values (e.g., PR number)

### Non-Goals

- **Authentication:** Hook doesn't handle credentials or API keys
- **Caching:** Hook doesn't cache or proxy requests
- **Transformation:** Hook doesn't modify tool inputs, only blocks them
- **Logging:** Hook doesn't persist block history (use Claude's logs)

## Token Budget Analysis

Based on current implementation:

**Per block in normal mode:**
- Message content: ~100-150 tokens (varies by route)
- No overhead (route name, URL, emoji removed)

**Per block in debug mode:**
- Debug header: ~15 tokens
- Matched URL: ~10-30 tokens (varies by URL length)
- Pattern display: ~10-20 tokens
- Message content: ~100-150 tokens
- **Total:** ~135-215 tokens

**Savings:** Approximately 35-50 tokens per block in normal mode vs debug mode.

With 10 blocks per session, this saves **350-500 tokens** without sacrificing functionality.

## Conclusion

The Tool Routing Hook implements a lightweight, token-efficient, and fail-safe mechanism to guide Claude toward better tools. Its design prioritizes:

- **Reliability** - Never break Claude's functionality
- **Efficiency** - Minimize token usage in normal operation
- **Usability** - Clear, actionable messages that Claude can execute immediately
- **Maintainability** - Declarative configuration and comprehensive tests

These principles ensure the hook adds value without becoming a maintenance burden or token sink.
