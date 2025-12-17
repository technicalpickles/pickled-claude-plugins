# MCP Error Handling Design

## Problem

When MCPProxy returns authentication or connection errors for upstream servers, Claude continues trying alternative approaches (retrying, trying other tools on the same server, falling back to WebFetch/curl). These retries waste time and tokens because the errors require user action outside of Claude.

## Example

```
Error: server 'slack' authentication failed for tool 'fetch'.
OAuth/token authentication required but not properly configured.
```

Claude's problematic response: "Let me try using WebFetch to access the Slack URL directly..."

## Solution

Add guidance to the existing `working-with-mcp` skill that teaches Claude to recognize unrecoverable errors and stop immediately.

## Implementation

### 1. Update Skill: `plugins/mcpproxy/skills/working-with-mcp/SKILL.md`

Add a subsection to "Red Flags - STOP Immediately" (after line 241, before "## Debugging MCPProxy Connection Issues"):

```markdown
### Red Flags in Error Responses

When an MCP tool call returns an error, check for these patterns. If matched, **STOP** - retrying won't help.

**Unrecoverable errors - STOP and tell the user:**

| Error Pattern | What It Means | Tell User |
|--------------|---------------|-----------|
| `authentication failed`, `OAuth/token authentication required`, `authorization required` | Upstream server needs re-auth | "Server '{name}' needs re-authentication. Run `mcpproxy auth login --server={name}` or use the MCPProxy system tray to re-authenticate." |
| `is not connected`, `is disabled` | Server offline/disabled | "Server '{name}' isn't connected. Check MCPProxy status." |
| `access_denied`, `insufficient_scope` | Missing permissions | "Server '{name}' lacks permissions. May need to re-authorize with additional scopes." |

**Why retrying won't help:**

These errors require user action outside of Claude:
- Re-running OAuth flow through MCPProxy
- Fixing server configuration
- Granting additional permissions

**Don't:**
- Retry the same tool with different parameters
- Try other tools on the same server (they'll fail too)
- Fall back to WebFetch/curl (won't have auth either)
```

### 2. Create Feature Gap Document: `docs/mcpproxy-feature-gaps.md`

Document MCPProxy functionality gaps discovered during this design:

- No MCP tool to trigger re-authentication for upstream servers
- User must use CLI (`mcpproxy auth login --server=X`) or system tray UI
- Could be improved with an MCP tool like `trigger_oauth(server_name)` that opens browser for re-auth

## Design Decisions

1. **Add to existing skill vs new skill** - Add to existing `working-with-mcp` skill for discoverability
2. **Placement** - Extend "Red Flags - STOP Immediately" section (progressive disclosure)
3. **Start simple** - Pattern list approach; can evolve to decision tree if needed
4. **Separate feature gaps** - Keep MCPProxy improvement ideas separate from skill content

## Error Categories

Based on MCPProxy source (`mcpproxy-go`), these error types indicate unrecoverable failures:

1. **Authentication/OAuth errors**: `authentication failed`, `OAuth/token authentication required`, `authorization required`, `invalid_token`, `Unauthorized`
2. **Connection state errors**: `is not connected`, `is currently connecting`, `is disabled`
3. **Permission errors**: `access_denied`, `insufficient_scope`

## Future Improvements

- **Option B**: Decision tree based on error fields (`server_name`, `troubleshooting`)
- **Option C**: Error category table with more granular actions
- **MCPProxy enhancement**: Add `trigger_oauth` MCP tool for in-session re-auth
