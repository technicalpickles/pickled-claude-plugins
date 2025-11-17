# Tool Routing Hook Design

**Date:** 2025-11-17
**Plugin:** dev-tools
**Status:** Approved

## Problem Statement

Claude frequently tries to use WebFetch for services that have better alternatives:
- Atlassian URLs should use MCP tools (authentication + structured data)
- GitHub PR URLs should use `gh pr view` (works for private PRs)
- Existing skill-based guidance is inconsistent (doesn't always activate)

We need enforcement, not just guidance.

## Solution Overview

A PreToolUse hook that intercepts WebFetch calls and blocks them with helpful messages when better tools exist.

**Scope:**
- 3 initial patterns: Atlassian, GitHub PRs
- JSON configuration for easy extensibility
- Hard blocking (exit 1) with clear error messages
- Fail-open error handling (broken hook won't break Claude)

## File Structure

```
plugins/dev-tools/
├── hooks/
│   ├── hooks.json                    # Hook registration
│   ├── tool-routes.json              # Service patterns (NEW)
│   └── check-tool-routing.py         # Pattern checker (NEW)
└── README.md                         # Documentation (UPDATE)
```

## Configuration Format

**hooks/tool-routes.json:**
```json
{
  "routes": {
    "atlassian": {
      "pattern": "https?://[^/]*\\.atlassian\\.net",
      "message": "Use Atlassian MCP tools for Jira/Confluence.\n\nCall: mcp__MCPProxy__retrieve_tools\nQuery: 'jira confluence atlassian issue'\n\nMCP tools provide authentication and structured data."
    },
    "github-pr": {
      "pattern": "github\\.com/[^/]+/[^/]+/pull/\\d+",
      "message": "Use `gh pr view <number>` for GitHub PRs.\n\nThis works for both public and private PRs and provides better formatting than HTML scraping."
    }
  }
}
```

**Design decisions:**
- Unique key per route (for reference/debugging)
- Standard Python regex patterns
- Multi-line messages for clarity
- No enable/disable flags - remove entry if unwanted
- Easy to extend: just add new entries

## Implementation

**hooks/check-tool-routing.py:**

Flow:
1. Load tool-routes.json from `${CLAUDE_PLUGIN_ROOT}/hooks/`
2. Read tool use data from stdin (JSON)
3. Extract URL from `tool_input.url`
4. Check against each pattern using `re.search()`
5. If match: print message to stderr, exit 1 (block)
6. If no match: exit 0 (allow)

**Error handling (fail-open):**
- Config missing → exit 0 + warning
- Invalid JSON → exit 0 + warning
- Invalid regex → skip route + warning
- Script crash → exit 0 (Python default)

**Size:** ~80 lines including error handling

## Hook Registration

**hooks/hooks.json:**
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "WebFetch",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/check-tool-routing.py"
          }
        ]
      }
    ]
  }
}
```

**Integration:**
- If hooks.json exists, merge this PreToolUse entry
- If not, create fresh

## Testing

Manual validation:
```bash
# Test Atlassian blocking
> "Fetch https://mycompany.atlassian.net/browse/PROJ-123"
# Expected: Block with Atlassian message

# Test GitHub PR blocking
> "Fetch https://github.com/user/repo/pull/42"
# Expected: Block with gh pr view message

# Test passthrough
> "Fetch https://example.com"
# Expected: Normal WebFetch execution
```

## Documentation

Add to `plugins/dev-tools/README.md`:

```markdown
## Tool Routing Hook

Automatically suggests better tools when Claude tries to WebFetch certain services.

**Configured services:**
- Atlassian (Jira/Confluence) → MCP tools
- GitHub PRs → `gh pr view`

**To add a service:** Edit `hooks/tool-routes.json`
```

## Future Extensibility (Not Implementing)

Could add later if needed:
- Severity levels (block vs warn)
- Per-route enable/disable flags
- Pattern matching on non-URL parameters
- Bash tool blocking (e.g., curl commands)

## Success Criteria

- [ ] Hook blocks Atlassian URLs with appropriate message
- [ ] Hook blocks GitHub PR URLs with appropriate message
- [ ] Hook allows unmatched URLs to pass through
- [ ] Broken config doesn't break Claude (fail-open works)
- [ ] Easy to add new routes (edit JSON only)

## Implementation Plan

1. Create `hooks/tool-routes.json` with 2 routes
2. Create `hooks/check-tool-routing.py` script (~80 lines)
3. Create or update `hooks/hooks.json` with PreToolUse entry
4. Make script executable (`chmod +x`)
5. Update `README.md` with documentation
6. Test all three scenarios
7. Commit and use
