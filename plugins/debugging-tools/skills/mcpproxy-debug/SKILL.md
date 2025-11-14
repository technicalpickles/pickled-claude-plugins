---
name: mcpproxy-debug
description: This skill should be used when debugging, configuring, or troubleshooting MCPProxy (smart-mcp-proxy/mcpproxy-go). It provides workflows for checking server status, diagnosing connection failures, fixing configuration issues, and understanding Docker isolation behavior.
---

# MCPProxy Debug

## Overview

MCPProxy is a Go-based smart proxy for Model Context Protocol (MCP) servers. This skill provides the capability to diagnose and fix MCPProxy issues systematically.

**Use this skill when:**
- MCPProxy server won't start or connect
- MCP servers show `connected: false` in status
- Docker isolation is causing failures
- Configuration changes aren't working
- Need to verify MCPProxy is running correctly

**Do NOT use this skill for:**
- Using MCPProxy tools normally → Use `dev-tools:using-mcpproxy-tools` instead

## Core Architecture (Quick Reference)

- **Core Server**: `mcpproxy` process at `127.0.0.1:8080` (default)
- **Config**: `~/.mcpproxy/mcp_config.json`
- **Logs**: `~/Library/Logs/mcpproxy/` (macOS) or `~/.mcpproxy/logs/` (Linux)
- **Database**: `~/.mcpproxy/config.db` (locked when running)

## Navigation Map - Start Here

Use this decision tree to find the right reference:

```
Problem: Where do I look?
├─ Server won't connect / shows errors
│  └─ Read: references/connection-failures.md
│
├─ Docker isolation issues / "not a TTY" errors
│  └─ Read: references/docker-isolation-guide.md
│
├─ Adding/configuring servers / config file questions
│  └─ Read: references/configuration-patterns.md
│
└─ Need detailed examples from real debugging sessions
   └─ Read: references/debugging-examples.md (already exists)
```

**Progressive disclosure principle**: Load only what you need. Start with the quick checks below. If those don't solve it, read the specific reference file.

## Quick Health Check (Do This First)

```bash
# 1. Is mcpproxy running?
ps aux | grep mcpproxy | grep -v grep

# 2. Get API key
grep '"api_key"' ~/.mcpproxy/mcp_config.json

# 3. Check server status
curl -s "http://127.0.0.1:8080/api/v1/servers?apikey=YOUR_KEY" | python3 -m json.tool

# 4. Check for recent errors
tail -50 ~/Library/Logs/mcpproxy/main.log | grep -i error
```

**Key status fields to check:**
- `connected`: Boolean - is the server connected?
- `status`: String - current state (connecting, ready, error)
- `last_error`: String - most recent error message
- `tool_count`: Number - how many tools available

**If status looks bad** → Read the appropriate reference file from Navigation Map above.

## Top 3 Common Issues (One-Line Fixes)

### 1. "the input device is not a TTY" (Docker servers)

**Fix:** Add `"isolation": {"enabled": false}` to the Docker-based server config.

**Why:** Docker isolation wraps Docker commands in Docker (Docker-in-Docker). See `references/docker-isolation-guide.md` for details.

### 2. "unexpected argument found" (uvx/npx servers)

**Fix:** Put package name as first arg: `["mcp-server-name", "--arg", "value"]`

**Why:** Package managers need package name first, then its arguments. See `references/configuration-patterns.md` for examples.

### 3. "Invalid or missing API key" after restart

**Fix:** Check `echo $MCPPROXY_API_KEY` - environment variable overrides config file.

**Why:** Tray app may set `MCPPROXY_API_KEY`. Get current key from logs: `grep "api_key_prefix" ~/Library/Logs/mcpproxy/main.log | tail -1`

## Essential Commands

### Restart MCPProxy
```bash
pkill mcpproxy
sleep 2
open /Applications/mcpproxy.app  # macOS
# OR
mcpproxy &  # Linux/headless
```

### Check Specific Server Logs
```bash
# See server-specific log (most revealing for connection issues)
tail -50 ~/Library/Logs/mcpproxy/server-SERVER_NAME.log

# Find errors in server log
grep -i "error\|stderr" ~/Library/Logs/mcpproxy/server-SERVER_NAME.log | tail -20
```

### Trigger Config Reload
```bash
# Touch config to trigger file watcher
touch ~/.mcpproxy/mcp_config.json

# Verify reload happened
grep -i "config.*reload" ~/Library/Logs/mcpproxy/main.log | tail -3
```

### Docker Container Check
```bash
# List MCPProxy containers
docker ps | grep mcpproxy

# Check container logs
docker logs CONTAINER_NAME
```

## Helper Scripts

Located in `scripts/` directory:

- **`check_status.sh`** - Quick health check of mcpproxy and all servers
- **`get_api_key.sh`** - Extract current API key from config or logs
- **`diagnose_server.sh SERVER_NAME`** - Comprehensive server diagnosis with error pattern detection
- **`compare_servers.sh WORKING BROKEN`** - Compare configs and status to find differences

Usage: `~/.claude/skills/mcpproxy-debug/scripts/SCRIPT_NAME.sh`

## References - Deep Dives

Load these on-demand when quick fixes don't solve the problem:

### `references/connection-failures.md`
**When to read:** Server shows `connected: false` or connection errors

**Contains:**
- Step-by-step connection diagnosis workflow
- Common error patterns with detailed explanations
- "context deadline exceeded" root cause analysis
- Server-specific log investigation techniques
- Real patterns: uvx args, Docker TTY, missing packages

### `references/docker-isolation-guide.md`
**When to read:** Docker isolation enabled and servers failing, or "not a TTY" errors

**Contains:**
- How Docker isolation works in MCPProxy
- Configuration options and defaults
- Docker-in-Docker prevention strategies
- Colima context support
- When to disable isolation (with examples)
- Volume mounting for file access

### `references/configuration-patterns.md`
**When to read:** Adding new servers or fixing config issues

**Contains:**
- Complete config structures for all server types
- uvx/npx package manager patterns
- Docker-based server patterns
- HTTP/SSE server patterns
- Common configuration mistakes with fixes
- Environment variable handling
- Quarantine settings

### `references/debugging-examples.md` (already exists)
**When to read:** Need detailed walkthroughs from real debugging sessions

**Contains:**
- Real-world case studies
- Complete diagnostic workflows with root cause analysis
- Pattern recognition guides for complex failure modes

## When to Load References

**Don't load references preemptively.** Use this workflow:

1. Run Quick Health Check (above)
2. Identify the problem category
3. Check Top 3 Common Issues for one-line fix
4. If not solved → Read the specific reference file from Navigation Map
5. Follow the detailed workflow in that reference

**Why:** Loading all references upfront = 4,000+ tokens of mostly irrelevant content. Progressive disclosure keeps context lean and relevant.

## Environment Variables Reference

- `MCPPROXY_API_KEY` - Set API key (overrides config file)
- `MCPPROXY_LISTEN` - Override bind address (e.g., `:8080`)
- `MCPPROXY_DEBUG` - Enable debug mode
- `HEADLESS` - Run without launching browser

**API Key Priority:** ENV var > config file > auto-generated

## Summary

This skill is a **navigation map**, not a documentation dump.

**Start with:**
1. Quick Health Check
2. Top 3 Common Issues

**If not solved:**
3. Use Navigation Map to find the right reference
4. Read only that reference file

**Result:** Fast diagnosis with minimal context overhead. Load ~1,400 tokens initially, then ~1,600 more only when needed for specific problems.
