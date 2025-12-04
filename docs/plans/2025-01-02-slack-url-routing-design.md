# Slack URL Routing Design

**Date:** 2025-01-02
**Status:** Approved

## Overview

Add tool routing to intercept Slack message URLs and redirect to Slack MCP tools. When Claude attempts to fetch a Slack thread URL via WebFetch, block the request and provide the parsed channel ID and timestamp for use with Slack MCP tools.

## Problem

Users share Slack URLs like `https://gustohq.slack.com/archives/C06TU4DH81K/p1764049181782629` and Claude attempts to scrape them with WebFetch. Slack MCP tools provide better access to message content with proper authentication and structured data.

## Solution

Extend the tool routing hook to:
1. Detect Slack message URLs
2. Parse channel ID and message timestamp
3. Convert timestamp format (remove `p` prefix, insert decimal)
4. Block WebFetch and suggest Slack MCP tools with extracted parameters

## Design Details

### URL Pattern Matching

Match Slack workspace URLs with message timestamps:
```regex
https?://[^/]+\.slack\.com/archives/([A-Z0-9]+)/p(\d{16})
```

Captures:
- Group 1: Channel ID (e.g., `C06TU4DH81K`)
- Group 2: Timestamp without decimal (e.g., `1764049181782629`)

Edge cases:
- Works with any Slack workspace domain (`*.slack.com`)
- Requires `/p` prefix to distinguish message links from channel-only URLs
- Only matches 16-digit timestamps (standard Slack format)

Won't match:
- Channel-only URLs like `https://workspace.slack.com/archives/C06TU4DH81K` (allowed through)

### Timestamp Conversion

Slack URLs encode timestamps as `p1764049181782629` (16 digits, no decimal).
Slack API expects `1764049181.782629` (decimal after 10th digit).

Conversion: `p1234567890123456` → `1234567890.123456`

### Message Format

```
Slack thread URL detected.

Channel: {channel_id}
Thread: {thread_ts}

Use Slack MCP to get thread messages.
```

Design rationale:
- Token-dense format (removes ~30 tokens vs verbose version)
- Provides parsed values ready to use
- Doesn't assume specific MCP tool names (varies by environment)
- Lets Claude discover and call appropriate Slack MCP tools
- Follows pattern of existing concise messages (e.g., github-pr)

### Implementation Changes

#### 1. New Parsing Function

Add `parse_slack_url(url, pattern)` to `check_tool_routing.py`:
- Extracts channel_id and timestamp using regex groups
- Converts timestamp format
- Returns dict with parsed values or None if parsing fails

#### 2. Enhanced Route Configuration

Add optional `parser` field to route config:
```json
{
  "slack-thread": {
    "pattern": "https?://[^/]+\\.slack\\.com/archives/([A-Z0-9]+)/p(\\d{16})",
    "parser": "slack_url",
    "message": "Slack thread URL detected.\n\nChannel: {channel_id}\nThread: {thread_ts}\n\nUse Slack MCP to get thread messages."
  }
}
```

#### 3. Hook Flow

1. WebFetch URL matches Slack pattern
2. Hook calls `parse_slack_url()` to extract values
3. Message template formatted with `{channel_id}` and `{thread_ts}`
4. Formatted message shown to Claude
5. Tool use blocked (exit code 2)

## Files to Modify

1. `plugins/dev-tools/hooks/check_tool_routing.py`
   - Add `parse_slack_url()` function
   - Enhance `check_url_patterns()` to support parsers
   - Add message template formatting

2. `plugins/dev-tools/hooks/tool-routes.json`
   - Add `slack-thread` route configuration

3. `plugins/dev-tools/hooks/fixtures/webfetch/slack-thread.json` (new)
   - Test fixture for Slack URL routing

## Testing

Create fixture with Slack URL:
- URL: `https://gustohq.slack.com/archives/C06TU4DH81K/p1764049181782629`
- Expected: Block with parsed channel_id and thread_ts
- Verify timestamp conversion is correct

Run with existing test infrastructure:
```bash
plugins/dev-tools/hooks/run_fixture.sh plugins/dev-tools/hooks/fixtures/webfetch/slack-thread.json
```

## Future Enhancements

- Support channel-only URLs (without message timestamp)
- Add parsing for other URL patterns (GitHub issues, JIRA tickets, etc.)
- Consider auto-redirect that calls MCP tools directly (more complex)
