# Docker Isolation - Complete Guide

**When to use this reference:** Docker isolation is enabled and servers are failing, or you see "not a TTY" errors.

This reference explains how MCPProxy's Docker isolation feature works and how to debug issues with it.

## What is Docker Isolation?

MCPProxy can run stdio MCP servers inside Docker containers for security isolation. This prevents untrusted servers from accessing your filesystem or network.

**Key concept:** MCPProxy wraps the server command in `docker run`, manages the container lifecycle, and handles stdio communication between Claude Code and the containerized server.

## How It Works

### Normal Flow (No Isolation)

```bash
# User configures:
command: "uvx"
args: ["mcp-server-sqlite", "--db-path", "/path/to/db"]

# MCPProxy runs directly:
uvx mcp-server-sqlite --db-path /path/to/db
```

### With Docker Isolation Enabled

```bash
# User configures same as above
# MCPProxy detects runtime (uvx → Python) and wraps in Docker:

docker run -i --rm \
  --memory="512m" \
  --cpus="1.0" \
  --network=bridge \
  python:3.11 \
  uvx mcp-server-sqlite --db-path /path/to/db
```

**MCPProxy automatically:**
1. Detects the runtime from the command (uvx→Python, npx→Node.js)
2. Selects appropriate Docker image
3. Wraps command in `docker run` with resource limits
4. Tracks container lifecycle
5. Cleans up container on exit

## Configuration

### Global Docker Isolation Settings

Located in `~/.mcpproxy/mcp_config.json`:

```json
{
  "docker_isolation": {
    "enabled": true,                    // Master switch
    "memory_limit": "512m",             // Per-container memory limit
    "cpu_limit": "1.0",                 // CPU cores (1.0 = 1 core)
    "timeout": "30s",                   // Container startup timeout
    "network_mode": "bridge",           // Docker network mode
    "default_images": {
      "uvx": "python:3.11",             // Image for uvx commands
      "npx": "node:20",                 // Image for npx commands
      "python": "python:3.11",          // Image for python commands
      "node": "node:20"                 // Image for node commands
    }
  }
}
```

### Per-Server Isolation Override

You can override isolation settings for specific servers:

```json
{
  "name": "my-server",
  "command": "uvx",
  "args": ["mcp-server-name"],
  "isolation": {
    "enabled": false,                   // Disable isolation for this server
    // OR customize settings:
    "enabled": true,
    "image": "python:3.12-slim",        // Custom image
    "memory_limit": "1g",               // More memory
    "cpu_limit": "2.0",                 // More CPU
    "network_mode": "none",             // No network access
    "working_dir": "/workspace"         // Working directory in container
  }
}
```

## Checking Docker Isolation Status

### Is Isolation Enabled for a Server?

```bash
# Check server log for isolation setup
grep -i "docker isolation enabled\|docker isolation setup" \
  ~/Library/Logs/mcpproxy/server-SERVER_NAME.log | tail -5

# Look for:
# "Docker isolation enabled for server: SERVER_NAME"
# "Docker isolation setup successful"
```

### View the Docker Command Being Used

```bash
# See actual docker run command
grep "docker_run_args" ~/Library/Logs/mcpproxy/main.log | tail -3

# Example output:
# docker_run_args: ["run", "-i", "--rm", "--memory=512m", "--cpus=1.0",
#                   "--network=bridge", "python:3.11", "uvx", "mcp-server-name"]
```

### List Running Containers

```bash
# List all MCPProxy containers
docker ps | grep mcpproxy

# Check specific server container
docker ps | grep mcpproxy-SERVER_NAME

# Check container health
docker inspect --format='{{.State.Status}}' CONTAINER_ID
```

### View Container Logs

```bash
# If container is running
docker logs CONTAINER_NAME

# If container exited, find it in history
docker ps -a | grep mcpproxy-SERVER_NAME
docker logs CONTAINER_ID
```

## Common Docker Isolation Issues

### Issue 1: Docker-in-Docker (Most Common)

**Symptom:** "the input device is not a TTY" error for Docker-based servers

**Root cause:** MCPProxy's Docker isolation wraps a Docker command in Docker, creating nested containers.

```json
// Server config uses Docker directly
{
  "command": "docker",
  "args": ["run", "-i", "--rm", "mcp-image:latest"]
}

// MCPProxy wraps it in another Docker (if isolation enabled):
docker run ... python:3.11 docker run -i --rm mcp-image:latest
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                           This fails: Docker-in-Docker
```

**Solution:** Explicitly disable isolation for Docker-based servers:

```json
{
  "name": "docker-server",
  "command": "docker",
  "args": ["run", "-i", "--rm", "mcp-image:latest"],
  "isolation": {
    "enabled": false  // CRITICAL: Always disable for Docker commands
  }
}
```

**Why explicit is better:** MCPProxy should auto-detect Docker commands and skip isolation, but explicit configuration is more reliable and prevents edge cases.

### Issue 2: File Access Problems

**Symptom:** Server can't access local files, permission errors

**Root cause:** Container can't access host filesystem by default.

**Solution 1: Disable isolation** (if file access is required):
```json
{
  "isolation": {
    "enabled": false
  }
}
```

**Solution 2: Mount volumes** (more secure):
```json
{
  "isolation": {
    "enabled": true,
    "volumes": [
      "/host/path:/container/path:ro"  // Read-only mount
    ]
  }
}
```

**Note:** Volume mounting requires MCPProxy support. Check documentation for current status.

### Issue 3: Network Access Blocked

**Symptom:** Server can't make API calls, network timeouts

**Root cause:** Container network mode blocks external access.

**Check current network mode:**
```bash
grep "network_mode" ~/.mcpproxy/mcp_config.json
```

**Solution:** Change network mode:
```json
{
  "isolation": {
    "enabled": true,
    "network_mode": "bridge"  // Default, allows external access
    // OR
    "network_mode": "host"    // Full host network access
    // OR
    "network_mode": "none"    // No network (most secure)
  }
}
```

### Issue 4: Container Image Not Found

**Symptom:** "context deadline exceeded", stderr shows "pull" or "not found"

**Investigation:**
```bash
# Check stderr for pull errors
grep -i "pull\|not found" ~/Library/Logs/mcpproxy/server-SERVER_NAME.log

# Try pulling image manually
docker pull python:3.11
```

**Solution:** Ensure Docker image exists locally or can be pulled:
```bash
# Pull image before starting mcpproxy
docker pull python:3.11

# Or specify a custom image that exists
{
  "isolation": {
    "image": "python:3.12-slim"  // Different image
  }
}
```

### Issue 5: Resource Limits Too Low

**Symptom:** Container exits unexpectedly, out of memory errors

**Investigation:**
```bash
# Check container exit status
docker ps -a | grep mcpproxy-SERVER_NAME

# Look for OOMKilled status
docker inspect CONTAINER_ID | grep -i "oom"
```

**Solution:** Increase resource limits:
```json
{
  "isolation": {
    "enabled": true,
    "memory_limit": "2g",     // Increase from default 512m
    "cpu_limit": "2.0"        // Increase from default 1.0
  }
}
```

## Docker Context Support (Colima)

MCPProxy uses your system's default Docker context. For Colima users:

```bash
# Check current Docker context
docker context show

# List all contexts
docker context ls

# Example output:
# NAME       DESCRIPTION                               DOCKER ENDPOINT
# default    Current DOCKER_HOST based configuration   unix:///var/run/docker.sock
# colima *   colima                                    unix:///Users/.../.colima/docker.sock

# MCPProxy uses whichever has the asterisk (*)
```

**To change context:**
```bash
docker context use colima
docker context use default
```

**After changing context:** Restart mcpproxy for changes to take effect.

## Disabling Docker Isolation

### Globally (All Servers)

Edit `~/.mcpproxy/mcp_config.json`:

```json
{
  "docker_isolation": {
    "enabled": false  // Disables for all servers
  }
}
```

### Per-Server (Recommended)

Only disable for servers that need it:

```json
{
  "name": "special-server",
  "command": "docker",  // Or any command that needs no isolation
  "args": ["..."],
  "isolation": {
    "enabled": false  // Only this server runs without isolation
  }
}
```

**Best practice:** Keep isolation enabled globally, disable per-server only when necessary.

## Debugging Workflow for Docker Isolation Issues

Use this systematic workflow:

### Step 1: Verify Isolation Status
```bash
# Is isolation enabled for this server?
grep -i "docker isolation" ~/Library/Logs/mcpproxy/server-SERVER_NAME.log | tail -5
```

### Step 2: Check Container Status
```bash
# Is container running?
docker ps | grep mcpproxy-SERVER_NAME

# Did container exit?
docker ps -a | grep mcpproxy-SERVER_NAME
```

### Step 3: View Container Logs
```bash
# Get container ID
CONTAINER_ID=$(docker ps -a | grep mcpproxy-SERVER_NAME | awk '{print $1}')

# View logs
docker logs $CONTAINER_ID
```

### Step 4: Check Docker Command
```bash
# See exact command being used
grep "docker_run_args" ~/Library/Logs/mcpproxy/main.log | tail -3
```

### Step 5: Test Manually
```bash
# Extract docker run command from logs and test it manually
# Example:
docker run -i --rm --memory=512m --cpus=1.0 python:3.11 uvx mcp-server-name
```

### Step 6: Apply Fix

Based on the issue:
- Docker-in-Docker → Disable isolation
- File access → Disable isolation or mount volumes
- Network issues → Change network_mode
- Resource limits → Increase memory/CPU
- Image not found → Pull image or change image

### Step 7: Reload and Verify
```bash
# Trigger config reload
touch ~/.mcpproxy/mcp_config.json

# Or restart
pkill mcpproxy && open /Applications/mcpproxy.app

# Verify fix
curl -s "http://127.0.0.1:8080/api/v1/servers?apikey=YOUR_KEY" | \
  python3 -m json.tool | grep -A 10 '"name": "SERVER_NAME"'
```

## When to Use Docker Isolation

### ✅ Use Docker Isolation When:
- Running untrusted third-party MCP servers
- Need security boundaries between servers
- Want resource limits per server
- Servers don't need host filesystem access
- Servers don't need special network configurations

### ❌ Disable Docker Isolation When:
- Server needs to access local files
- Server command is already Docker (prevents Docker-in-Docker)
- Server needs host network access
- Troubleshooting connection issues
- Performance is critical (isolation adds overhead)

## Quick Reference

### Check if isolation is active
```bash
grep -i "docker isolation" ~/Library/Logs/mcpproxy/server-NAME.log | tail -5
```

### List containers
```bash
docker ps | grep mcpproxy
```

### View container logs
```bash
docker logs CONTAINER_NAME
```

### Disable isolation for server
```json
{"isolation": {"enabled": false}}
```

### Increase resources
```json
{"isolation": {"memory_limit": "2g", "cpu_limit": "2.0"}}
```

### Change network mode
```json
{"isolation": {"network_mode": "host"}}
```

### Use custom image
```json
{"isolation": {"image": "python:3.12-slim"}}
```

## Summary

Docker isolation provides security but adds complexity. Start with isolation disabled while getting servers working, then enable it once everything is stable. Always disable isolation explicitly for Docker-based servers to prevent Docker-in-Docker issues.
