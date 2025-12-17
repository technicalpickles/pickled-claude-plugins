# MCPProxy Feature Gaps

Feature requests and improvement ideas for MCPProxy, discovered while building Claude Code plugins.

## MCP Tool for Upstream Server Re-Authentication

**Problem**: When an upstream server (e.g., Slack) returns an OAuth/authentication error, Claude cannot help the user re-authenticate within the session. The user must manually run `mcpproxy auth login --server=X` or use the system tray UI.

**Current behavior**:
- MCPProxy returns error: `server 'slack' authentication failed for tool 'fetch'. OAuth/token authentication required...`
- Claude can only tell user to run CLI command or use system tray
- User must leave Claude, run command, return to Claude

**Proposed solution**: Add an MCP tool to trigger OAuth re-authentication:

```
mcp__MCPProxy__trigger_auth(server_name: "slack")
```

Behavior:
1. Opens browser to OAuth provider's login page (like `mcpproxy auth login` does)
2. Returns immediately with status "authentication flow started"
3. User completes OAuth in browser
4. MCPProxy updates token automatically
5. Claude can retry the original tool call

**Workaround today**: User runs `mcpproxy auth login --server=X` in separate terminal.

**Related**: MCPProxy has HTTP API endpoint `POST /servers/{name}/login` but no MCP tool equivalent.

---

## Add More Feature Gaps Here

When you discover functionality that would improve the MCPProxy + Claude Code integration, document it here with:
- Problem description
- Current behavior
- Proposed solution
- Workaround today
