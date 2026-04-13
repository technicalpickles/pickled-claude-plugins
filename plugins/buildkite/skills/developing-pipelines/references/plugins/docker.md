# Docker Buildkite Plugin

**Source:** https://github.com/buildkite-plugins/docker-buildkite-plugin
**Version documented:** v5.13.0

## Overview

Runs pipeline steps inside Docker containers. Supports automatic checkout mounting, environment propagation, and volume mounts.

## Configuration Options

### Required

| Option | Type | Description |
|--------|------|-------------|
| `image` | string | Docker image name (e.g., `node:20`, `golang:1.21`) |

### Common Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `command` | array | - | Command to run (sets shell to false) |
| `entrypoint` | string | - | Override image's default entrypoint |
| `environment` | array | - | Additional environment variables |
| `env-file` | array | - | Files to load as environment variables |
| `volumes` | array | - | Volume mounts (`host:container`) |
| `workdir` | string | - | Working directory inside container |
| `user` | string | - | User to run as inside container |
| `always-pull` | boolean | false | Always pull latest image before running |
| `mount-checkout` | boolean | true | Mount current working directory |
| `propagate-environment` | boolean | false | Propagate all pipeline environment variables |

### Resource Limits

| Option | Type | Description |
|--------|------|-------------|
| `memory` | string | Memory limit (e.g., `2g`) |
| `memory-swap` | string | Swap limit |
| `memory-swappiness` | integer | Memory swappiness (0-100) |
| `cpus` | string | Number of CPUs |
| `device-read-bps` | array | Limit read rate from device |
| `device-write-bps` | array | Limit write rate to device |

### Networking

| Option | Type | Description |
|--------|------|-------------|
| `network` | string | Docker network to connect to |
| `add-host` | array | Additional /etc/hosts entries |
| `publish` | array | Publish ports (`host:container`) |

### Security

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `privileged` | boolean | false | Run in privileged mode |
| `init` | boolean | true | Run init process inside container |
| `propagate-uid-gid` | boolean | false | Match container UID/GID to host user |
| `propagate-aws-auth-tokens` | boolean | false | Propagate AWS auth environment |
| `propagate-gcp-auth-tokens` | boolean | false | Propagate GCP auth credentials |

### Other

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `debug` | boolean | false | Output full Docker commands |
| `shell` | array/boolean | - | Shell to use for commands |
| `leave-container` | boolean | false | Don't remove container after run |
| `load` | string | - | Load Docker image from file |

## Examples

**Basic usage:**
```yaml
steps:
  - command: "npm test"
    plugins:
      - docker#v5.13.0:
          image: "node:20"
```

**With environment and volumes:**
```yaml
steps:
  - command: "yarn install && yarn test"
    plugins:
      - docker#v5.13.0:
          image: "node:20"
          environment:
            - "NODE_ENV=test"
            - "CI=true"
          volumes:
            - "./cache:/app/cache"
```

**Docker-in-Docker:**
```yaml
steps:
  - command: "docker build -t myapp ."
    plugins:
      - docker#v5.13.0:
          image: "docker:latest"
          privileged: true
          volumes:
            - "/var/run/docker.sock:/var/run/docker.sock"
```

## Version-Specific Docs

For specific versions: https://github.com/buildkite-plugins/docker-buildkite-plugin/tree/{version}
