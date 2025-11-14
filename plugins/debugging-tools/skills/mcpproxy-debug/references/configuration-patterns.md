# Configuration Patterns - Complete Reference

**When to use this reference:** Adding new MCP servers to MCPProxy or fixing configuration issues.

This reference provides complete configuration structures for all server types with detailed explanations.

## Configuration File Location

`~/.mcpproxy/mcp_config.json`

**Important:** After editing, trigger reload:
```bash
touch ~/.mcpproxy/mcp_config.json
# OR restart mcpproxy
pkill mcpproxy && open /Applications/mcpproxy.app
```

## Complete Configuration Patterns

### Pattern 1: uvx/npx Servers (Package Managers)

**Key rule:** Package name MUST be first argument.

```json
{
  "mcpServers": {
    "server-name": {
      "protocol": "stdio",
      "command": "uvx",           // or "npx"
      "args": [
        "package-name",           // CRITICAL: Package name FIRST
        "--arg1",                 // Then package arguments
        "value1",
        "--arg2",
        "value2"
      ],
      "env": {
        // Optional environment variables
        "API_KEY": "secret",
        "DEBUG": "true"
      },
      "working_dir": "/path/to/dir",  // Optional working directory
      "enabled": true,
      "quarantined": false
    }
  }
}
```

**Real examples:**

#### Time Server with Timezone
```json
{
  "time": {
    "protocol": "stdio",
    "command": "uvx",
    "args": [
      "mcp-server-time",
      "--local-timezone",
      "America/New_York"
    ],
    "enabled": true,
    "quarantined": false
  }
}
```

#### SQLite Server with Database Path
```json
{
  "sqlite": {
    "protocol": "stdio",
    "command": "uvx",
    "args": [
      "mcp-server-sqlite",
      "--db-path",
      "/Users/username/data/mydb.sqlite"
    ],
    "enabled": true,
    "quarantined": false
  }
}
```

#### Filesystem Server with Paths
```json
{
  "filesystem": {
    "protocol": "stdio",
    "command": "npx",
    "args": [
      "@modelcontextprotocol/server-filesystem",
      "/Users/username/workspace",
      "/Users/username/Documents"
    ],
    "enabled": true,
    "quarantined": false
  }
}
```

**Common mistakes:**
```json
// ❌ WRONG - Arguments before package name
{
  "command": "uvx",
  "args": ["--local-timezone", "America/New_York"]
  // Error: "unexpected argument '--local-timezone' found"
}

// ✅ CORRECT - Package name first
{
  "command": "uvx",
  "args": ["mcp-server-time", "--local-timezone", "America/New_York"]
}
```

### Pattern 2: Docker-Based Servers

**Key rules:**
1. Use `-i` (NOT `-it`) for stdin pipe
2. ALWAYS disable isolation to prevent Docker-in-Docker

```json
{
  "docker-server": {
    "protocol": "stdio",
    "command": "docker",
    "args": [
      "run",
      "-i",                    // CRITICAL: -i only, not -it
      "--rm",                  // Clean up container after exit
      "-e", "VAR_NAME",        // Pass environment variables
      "image:tag",             // Docker image
      "subcommand"             // Optional: server entrypoint
    ],
    "env": {
      "VAR_NAME": "value"      // Values for -e flags
    },
    "isolation": {
      "enabled": false         // CRITICAL: Disable to prevent Docker-in-Docker
    },
    "enabled": true,
    "quarantined": false
  }
}
```

**Real examples:**

#### Basic Docker MCP Server
```json
{
  "docker-mcp": {
    "protocol": "stdio",
    "command": "docker",
    "args": [
      "run",
      "-i",
      "--rm",
      "ghcr.io/example/mcp-server:latest"
    ],
    "isolation": {
      "enabled": false
    },
    "enabled": true,
    "quarantined": false
  }
}
```

#### Docker Server with Environment Variables
```json
{
  "api-server": {
    "protocol": "stdio",
    "command": "docker",
    "args": [
      "run",
      "-i",
      "--rm",
      "-e", "API_KEY",
      "-e", "API_URL",
      "mycompany/api-mcp:v1.0"
    ],
    "env": {
      "API_KEY": "sk-xxxx",
      "API_URL": "https://api.example.com"
    },
    "isolation": {
      "enabled": false
    },
    "enabled": true,
    "quarantined": false
  }
}
```

#### Docker Server with Volume Mounts
```json
{
  "file-processor": {
    "protocol": "stdio",
    "command": "docker",
    "args": [
      "run",
      "-i",
      "--rm",
      "-v", "/Users/username/data:/data:ro",
      "mycompany/file-mcp:latest",
      "--data-dir", "/data"
    ],
    "isolation": {
      "enabled": false
    },
    "enabled": true,
    "quarantined": false
  }
}
```

**Common mistakes:**
```json
// ❌ WRONG - Using -it flags
{
  "command": "docker",
  "args": ["run", "-it", "--rm", "image:tag"]
  // Error: "the input device is not a TTY"
}

// ❌ WRONG - Isolation enabled
{
  "command": "docker",
  "args": ["run", "-i", "--rm", "image:tag"],
  "isolation": {"enabled": true}
  // Error: Docker-in-Docker, "not a TTY"
}

// ✅ CORRECT - Use -i only, disable isolation
{
  "command": "docker",
  "args": ["run", "-i", "--rm", "image:tag"],
  "isolation": {"enabled": false}
}
```

### Pattern 3: HTTP/SSE Servers

For servers accessed via HTTP or Server-Sent Events.

```json
{
  "http-server": {
    "protocol": "http",        // or "sse"
    "url": "https://api.example.com/mcp",
    "headers": {
      // Optional authentication headers
      "Authorization": "Bearer token",
      "X-API-Key": "secret"
    },
    "enabled": true,
    "quarantined": false
  }
}
```

**Real examples:**

#### HTTP Server with Bearer Token
```json
{
  "remote-api": {
    "protocol": "http",
    "url": "https://mcp.example.com/v1",
    "headers": {
      "Authorization": "Bearer sk-xxxxxxxxxxxx"
    },
    "enabled": true,
    "quarantined": false
  }
}
```

#### SSE Server with API Key
```json
{
  "streaming-api": {
    "protocol": "sse",
    "url": "https://stream.example.com/mcp",
    "headers": {
      "X-API-Key": "api-key-here"
    },
    "enabled": true,
    "quarantined": false
  }
}
```

#### HTTP Server Without Authentication
```json
{
  "public-api": {
    "protocol": "http",
    "url": "http://localhost:3000/mcp",
    "enabled": true,
    "quarantined": false
  }
}
```

### Pattern 4: Local Command Servers

For locally installed commands (not uvx/npx).

```json
{
  "local-server": {
    "protocol": "stdio",
    "command": "/usr/local/bin/mcp-server",  // Full path or command in PATH
    "args": [
      "--config", "/path/to/config.json",
      "--verbose"
    ],
    "env": {
      "HOME": "/Users/username",
      "PYTHONPATH": "/path/to/modules"
    },
    "working_dir": "/Users/username/workspace",
    "enabled": true,
    "quarantined": false
  }
}
```

**Real examples:**

#### Python Script as Server
```json
{
  "custom-python": {
    "protocol": "stdio",
    "command": "python",
    "args": [
      "/Users/username/mcp-servers/my_server.py",
      "--config", "production"
    ],
    "env": {
      "PYTHONUNBUFFERED": "1"
    },
    "working_dir": "/Users/username/mcp-servers",
    "enabled": true,
    "quarantined": false
  }
}
```

#### Node.js Script as Server
```json
{
  "custom-node": {
    "protocol": "stdio",
    "command": "node",
    "args": [
      "/Users/username/mcp-servers/server.js"
    ],
    "env": {
      "NODE_ENV": "production"
    },
    "working_dir": "/Users/username/mcp-servers",
    "enabled": true,
    "quarantined": false
  }
}
```

## Complete Configuration File Structure

```json
{
  "api_key": "mcpproxy-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "listen": "127.0.0.1:8080",
  "docker_isolation": {
    "enabled": true,
    "memory_limit": "512m",
    "cpu_limit": "1.0",
    "timeout": "30s",
    "network_mode": "bridge",
    "default_images": {
      "uvx": "python:3.11",
      "npx": "node:20",
      "python": "python:3.11",
      "node": "node:20"
    }
  },
  "mcpServers": {
    "server1": {
      "protocol": "stdio",
      "command": "uvx",
      "args": ["package-name"],
      "enabled": true,
      "quarantined": false
    },
    "server2": {
      "protocol": "http",
      "url": "https://api.example.com",
      "enabled": true,
      "quarantined": false
    }
  }
}
```

## Common Configuration Mistakes

### 1. Missing Package Name (uvx/npx)
```json
// ❌ WRONG
{"command": "uvx", "args": ["--arg", "value"]}

// ✅ CORRECT
{"command": "uvx", "args": ["package-name", "--arg", "value"]}
```

### 2. Wrong Docker Flags
```json
// ❌ WRONG - Using -it
{"command": "docker", "args": ["run", "-it", "--rm", "image"]}

// ✅ CORRECT - Using -i only
{"command": "docker", "args": ["run", "-i", "--rm", "image"]}
```

### 3. Docker Isolation Not Disabled
```json
// ❌ WRONG - Isolation enabled for Docker
{
  "command": "docker",
  "args": ["run", "-i", "--rm", "image"],
  "isolation": {"enabled": true}  // Docker-in-Docker!
}

// ✅ CORRECT - Isolation disabled
{
  "command": "docker",
  "args": ["run", "-i", "--rm", "image"],
  "isolation": {"enabled": false}
}
```

### 4. Wrong Protocol for Server Type
```json
// ❌ WRONG - Using stdio for URL
{"protocol": "stdio", "url": "https://api.example.com"}

// ❌ WRONG - Using http for command
{"protocol": "http", "command": "uvx", "args": ["package"]}

// ✅ CORRECT - Match protocol to type
{"protocol": "http", "url": "https://api.example.com"}
{"protocol": "stdio", "command": "uvx", "args": ["package"]}
```

### 5. Server Still Quarantined
```json
// ❌ WRONG - Quarantine prevents execution
{
  "command": "uvx",
  "args": ["package"],
  "quarantined": true  // Tools return security analysis!
}

// ✅ CORRECT - Set to false to use tools
{
  "command": "uvx",
  "args": ["package"],
  "quarantined": false
}
```

### 6. Invalid JSON
```json
// ❌ WRONG - Trailing comma
{
  "command": "uvx",
  "args": ["package"],
  "enabled": true,  // Trailing comma breaks JSON
}

// ✅ CORRECT - No trailing comma
{
  "command": "uvx",
  "args": ["package"],
  "enabled": true
}
```

## Environment Variables

### Built-in Environment Variables

MCPProxy automatically provides:
- `HOME` - User's home directory
- `PATH` - System PATH

### Custom Environment Variables

Add via `env` field:
```json
{
  "env": {
    "API_KEY": "secret",
    "DEBUG": "true",
    "CUSTOM_VAR": "value"
  }
}
```

### Environment Variable Priority

For Docker servers:
1. Variables in Docker args (`-e VAR=value`)
2. Variables in `env` field passed via `-e VAR` (value from env)
3. Host environment (if not overridden)

**Example:**
```json
{
  "command": "docker",
  "args": [
    "run", "-i", "--rm",
    "-e", "API_KEY",           // Value from env field
    "-e", "DEBUG=true",        // Value in args
    "image:tag"
  ],
  "env": {
    "API_KEY": "secret"        // Used by -e API_KEY above
  }
}
```

## Quarantine Settings

New servers are automatically quarantined for security. To use them:

```json
{
  "quarantined": false  // Set to false to enable tool execution
}
```

**What quarantine does:**
- `quarantined: true` - Tools return security analysis instead of executing
- `quarantined: false` - Tools execute normally

**Best practice:** Review new servers before setting `quarantined: false`.

## Docker Isolation Configuration

See `references/docker-isolation-guide.md` for detailed Docker isolation configuration.

**Quick reference:**

```json
{
  // Global settings
  "docker_isolation": {
    "enabled": true,              // Master switch
    "memory_limit": "512m",       // Default memory per container
    "cpu_limit": "1.0",           // Default CPU per container
    "network_mode": "bridge"      // Default network mode
  },

  // Per-server override
  "mcpServers": {
    "my-server": {
      "isolation": {
        "enabled": false,         // Disable isolation
        // OR customize:
        "enabled": true,
        "image": "python:3.12",
        "memory_limit": "1g",
        "cpu_limit": "2.0",
        "network_mode": "host"
      }
    }
  }
}
```

## Verification After Configuration

After adding or modifying server configuration:

```bash
# 1. Trigger reload
touch ~/.mcpproxy/mcp_config.json

# 2. Wait for connection (30 seconds)
sleep 30

# 3. Check server status
curl -s "http://127.0.0.1:8080/api/v1/servers?apikey=YOUR_KEY" | \
  python3 -m json.tool | grep -A 10 '"name": "SERVER_NAME"'

# 4. Verify connection
# Look for:
#   "connected": true
#   "status": "ready"
#   "tool_count": > 0

# 5. If not connected, check logs
tail -50 ~/Library/Logs/mcpproxy/server-SERVER_NAME.log
```

## Configuration Checklist

When adding a new server, verify:

- [ ] JSON is valid (no trailing commas, quotes matched)
- [ ] Protocol matches server type (stdio/http/sse)
- [ ] For uvx/npx: Package name is first argument
- [ ] For Docker: Using `-i` not `-it`
- [ ] For Docker: Isolation disabled (`"enabled": false`)
- [ ] `enabled` is set to `true`
- [ ] `quarantined` is set to `false` (after review)
- [ ] Environment variables defined if needed
- [ ] Config file reloaded (touch or restart)
- [ ] Server status shows `connected: true` (wait 30s)

If server won't connect, see `references/connection-failures.md` for debugging.

## Summary

Configuration patterns vary by server type. The most common mistakes are:
1. Missing package name for uvx/npx
2. Using `-it` instead of `-i` for Docker
3. Leaving isolation enabled for Docker-based servers
4. Leaving servers quarantined

Follow the pattern for your server type, verify with the checklist, and check logs if it doesn't connect.
