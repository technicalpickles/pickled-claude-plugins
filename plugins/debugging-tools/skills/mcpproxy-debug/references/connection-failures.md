# Connection Failures - Detailed Diagnosis

**When to use this reference:** Server shows `connected: false` or has connection errors in status API.

This reference provides step-by-step workflows for diagnosing why an MCP server won't connect through MCPProxy.

## Systematic Diagnosis Workflow

### Step 1: Check Server-Specific Logs

Server-specific logs contain the most revealing information, especially stderr output from the failing server.

```bash
# List all server logs (most recent first)
ls -lhrt ~/Library/Logs/mcpproxy/server-*.log | tail -10

# Check specific server log (last 50 lines)
tail -50 ~/Library/Logs/mcpproxy/server-SERVER_NAME.log

# Find errors in server log
grep -i "error\|failed\|stderr" ~/Library/Logs/mcpproxy/server-SERVER_NAME.log | tail -20

# Focus on stderr (most revealing)
grep "stderr" ~/Library/Logs/mcpproxy/server-SERVER_NAME.log | tail -20
```

**What to look for:**
- Error messages in stderr output
- Stack traces indicating crashes
- Missing dependencies or packages
- Permission errors
- Network connection failures

### Step 2: Identify Error Patterns

Most connection failures follow recognizable patterns. Match the error message to the pattern below.

## Common Error Patterns

### Pattern: "unexpected argument found"

**Example stderr:**
```
error: unexpected argument '--local-timezone' found
```

**Root cause:** Package manager (uvx/npx) received server arguments before package name.

**Commands affected:** `uvx`, `npx`, `yarn dlx`, `bunx`

**How it happens:**
```json
// WRONG - Arguments passed to uvx instead of the package
{
  "command": "uvx",
  "args": ["--local-timezone", "America/New_York"]
}

// Package manager sees: uvx --local-timezone America/New_York
// And thinks: "--local-timezone is not a uvx option!"
```

**Fix:**
```json
// CORRECT - Package name first, then its arguments
{
  "command": "uvx",
  "args": [
    "mcp-server-time",           // Package name FIRST
    "--local-timezone",          // Then package's arguments
    "America/New_York"
  ]
}
```

**Verification:**
```bash
# After fixing config, check server log for successful connection
tail -20 ~/Library/Logs/mcpproxy/server-SERVER_NAME.log | grep -i "connected\|ready"
```

### Pattern: "the input device is not a TTY"

**Example stderr:**
```
the input device is not a TTY
```

**Root causes:**

#### Cause 1: Using `-it` with Docker

MCPProxy communicates via stdio pipes, not terminal TTY sessions. Using `-it` with Docker tries to allocate a TTY, which fails in pipe mode.

```json
// WRONG - Docker with -it flags
{
  "command": "docker",
  "args": ["run", "-it", "--rm", "image:tag"]
}
```

**Fix:**
```json
// CORRECT - Only -i for stdin pipe
{
  "command": "docker",
  "args": ["run", "-i", "--rm", "image:tag"]
}
```

#### Cause 2: Docker Isolation on Docker-based Server

MCPProxy's Docker isolation feature wraps commands in Docker containers. When the command itself is Docker, you get Docker-in-Docker, which causes TTY issues.

```json
// WRONG - Docker isolation wrapping a Docker command
{
  "command": "docker",
  "args": ["run", "-i", "--rm", "image:tag"],
  "isolation": {
    "enabled": true  // This wraps Docker in Docker!
  }
}
```

**Fix:**
```json
// CORRECT - Disable isolation for Docker commands
{
  "command": "docker",
  "args": ["run", "-i", "--rm", "image:tag"],
  "isolation": {
    "enabled": false
  }
}
```

**Why this happens:** MCPProxy auto-detects Docker commands and should skip isolation, but explicit configuration is more reliable.

**Verification:**
```bash
# Check if isolation was applied
grep -i "docker isolation" ~/Library/Logs/mcpproxy/server-SERVER_NAME.log | tail -5

# Verify no Docker containers running for this server
docker ps | grep mcpproxy-SERVER_NAME
```

### Pattern: "context deadline exceeded"

**Example error:**
```
last_error: "context deadline exceeded"
status: "error"
```

**Root cause:** Server failed to initialize within timeout (usually 30 seconds).

**Common reasons:**

1. **Underlying error hidden** - Check stderr for the real error:
   ```bash
   grep "stderr" ~/Library/Logs/mcpproxy/server-SERVER_NAME.log | tail -20
   ```

2. **Missing package name** (uvx/npx) - Look for "unexpected argument":
   ```bash
   grep "unexpected argument" ~/Library/Logs/mcpproxy/server-SERVER_NAME.log
   ```

3. **Docker TTY issue** - Look for "not a TTY":
   ```bash
   grep "TTY" ~/Library/Logs/mcpproxy/server-SERVER_NAME.log
   ```

4. **Docker image pull failed**:
   ```bash
   grep -i "pull\|not found" ~/Library/Logs/mcpproxy/server-SERVER_NAME.log
   ```

5. **Server crashed during startup**:
   ```bash
   grep -i "stack trace\|panic\|exception" ~/Library/Logs/mcpproxy/server-SERVER_NAME.log
   ```

6. **Missing environment variables**:
   ```bash
   grep -i "missing\|required.*variable" ~/Library/Logs/mcpproxy/server-SERVER_NAME.log
   ```

7. **Network issues** (HTTP servers):
   ```bash
   grep -i "connection refused\|timeout" ~/Library/Logs/mcpproxy/server-SERVER_NAME.log
   ```

**Investigation workflow:**

```bash
# 1. Check if process even started
grep "Starting connection\|Docker isolation setup" ~/Library/Logs/mcpproxy/server-SERVER_NAME.log | tail -5

# 2. Check stderr for the real error
grep "stderr" ~/Library/Logs/mcpproxy/server-SERVER_NAME.log | tail -20

# 3. If Docker isolation enabled, check container logs
docker ps -a | grep mcpproxy-SERVER_NAME
docker logs CONTAINER_ID

# 4. Check Docker command being executed
grep "docker_run_args" ~/Library/Logs/mcpproxy/server-SERVER_NAME.log | tail -3
```

**Fix:** Address the underlying error found in stderr.

### Pattern: "database is locked"

**Example error:**
```
ERROR: database is locked
```

**Root cause:** Another mcpproxy instance is running and has locked `~/.mcpproxy/config.db`.

**Fix:**
```bash
# Kill all mcpproxy instances
pkill mcpproxy

# Wait for processes to clean up
sleep 2

# Verify no mcpproxy processes remain
ps aux | grep mcpproxy | grep -v grep

# Restart mcpproxy
open /Applications/mcpproxy.app  # macOS
# OR
mcpproxy &  # Linux/headless
```

**Prevention:** Always use `pkill mcpproxy` before starting a new instance.

### Pattern: "transport error" / "EOF"

**Example error:**
```
last_error: "transport error: EOF"
```

**Root cause:** Server process exited unexpectedly or closed stdio pipes.

**Investigation:**
```bash
# Check if server crashed
grep -i "exit\|crash\|terminated" ~/Library/Logs/mcpproxy/server-SERVER_NAME.log | tail -10

# Look for error messages before EOF
grep -B 20 "EOF" ~/Library/Logs/mcpproxy/server-SERVER_NAME.log | tail -30

# Check stderr for crash details
grep "stderr" ~/Library/Logs/mcpproxy/server-SERVER_NAME.log | tail -20
```

**Common causes:**
- Missing dependencies in Docker image
- Server code bug causing crash
- Memory/resource limits hit (Docker isolation)
- Permission errors accessing files

**Fix:** Depends on stderr output. Often requires fixing server code or Docker image.

## Step 3: Docker Isolation Checks

If Docker isolation is enabled and server is failing:

```bash
# Check if isolation is active for this server
grep -i "docker isolation enabled\|docker isolation setup" ~/Library/Logs/mcpproxy/server-SERVER_NAME.log | tail -5

# List running containers
docker ps | grep mcpproxy

# Check container status
docker ps -a | grep mcpproxy-SERVER_NAME

# View container logs
docker logs CONTAINER_NAME

# Check Docker context (for Colima users)
docker context show
```

**If Docker isolation is interfering:**
1. See `references/docker-isolation-guide.md` for detailed Docker troubleshooting
2. Consider disabling isolation for this server (add `"isolation": {"enabled": false}`)

## Step 4: Configuration Verification

Verify the server configuration is correct:

```bash
# View server config (pretty-printed)
cat ~/.mcpproxy/mcp_config.json | python3 -m json.tool | grep -A 20 '"name": "SERVER_NAME"'

# Check for common mistakes:
# - uvx/npx: Package name is first argument?
# - Docker: Using -i not -it?
# - Docker servers: isolation disabled?
# - Quarantined: "quarantined": false?
```

For detailed configuration patterns, see `references/configuration-patterns.md`.

## Step 5: Test Server Command Manually

Test if the server command works outside MCPProxy:

```bash
# For uvx servers
uvx mcp-server-name --arg value

# For Docker servers (remove -i for manual testing)
docker run --rm -it image:tag

# For npx servers
npx mcp-server-name --arg value
```

**What to look for:**
- Does the command fail with same error?
- Is the package/image available?
- Are arguments correct?

## Debugging Checklist

Use this checklist systematically:

- [ ] Checked server-specific log for errors
- [ ] Examined stderr output (most revealing)
- [ ] Matched error to common patterns above
- [ ] Verified command syntax (uvx: package name first, Docker: -i not -it)
- [ ] Checked Docker isolation status (disabled for Docker commands?)
- [ ] Verified configuration file is valid JSON
- [ ] Tested command manually outside MCPProxy
- [ ] Triggered config reload (touch config file or restart mcpproxy)
- [ ] Waited 30 seconds for connection to initialize
- [ ] Checked main.log for global errors

If all checks pass and server still won't connect, see `references/debugging-examples.md` for real-world case studies.

## Success Verification

After fixing the issue:

```bash
# 1. Check server status via API
curl -s "http://127.0.0.1:8080/api/v1/servers?apikey=YOUR_KEY" | python3 -m json.tool | grep -A 10 '"name": "SERVER_NAME"'

# Look for:
# "connected": true
# "status": "ready"
# "tool_count": > 0

# 2. Check server log for successful connection
tail -20 ~/Library/Logs/mcpproxy/server-SERVER_NAME.log | grep -i "connected\|ready\|discovered"

# 3. Verify tools are available
curl -s "http://127.0.0.1:8080/api/v1/tools?apikey=YOUR_KEY" | python3 -m json.tool | grep "SERVER_NAME:"
```

If `connected: true` and `tool_count > 0`, the issue is resolved.
