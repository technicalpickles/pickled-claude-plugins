# Docker Context Integration

## How Colima Creates Contexts

Each Colima profile creates a corresponding Docker context:

| Colima Profile | Docker Context |
|----------------|----------------|
| `default` | `colima` |
| `work` | `colima-work` |
| `<name>` | `colima-<name>` |

Colima sets itself as the default context on startup.

## Switching Contexts

### Global Switch (Persistent)

Stored in `~/.docker/config.json` under `currentContext`. Affects all terminals.

```bash
# List available contexts
docker context list

# Switch globally
docker context use colima-work
```

### Per-Session Override

```bash
export DOCKER_CONTEXT=colima-work
```

### Per-Command Override

```bash
docker --context colima-work ps
docker --context colima-work build -t myimage .
```

## Getting the Socket Path

Some applications don't respect Docker contexts and need `DOCKER_HOST` set explicitly.

```bash
# View full status including socket
colima status -p <profile>

# Extract just the socket path
colima status -p <profile> --json | jq -r .docker_socket

# Set DOCKER_HOST for non-context-aware apps
export DOCKER_HOST="unix://$(colima status -p work --json | jq -r .docker_socket)"
```

## Socket Locations

- Default profile: `~/.colima/default/docker.sock`
- Named profile: `~/.colima/<profile>/docker.sock`

## Running Multiple Profiles Simultaneously

You can run multiple Colima profiles at once, each with its own Docker context:

```bash
colima start default
colima start work --cpu 4 --memory 8

# Now both contexts exist
docker context list
# NAME          DESCRIPTION  DOCKER ENDPOINT
# colima        colima       unix:///.../.colima/default/docker.sock
# colima-work   colima       unix:///.../.colima/work/docker.sock
```

Switch between them as needed, or use per-command `--context` flags.
