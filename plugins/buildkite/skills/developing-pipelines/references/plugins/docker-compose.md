# Docker Compose Buildkite Plugin

**Source:** https://github.com/buildkite-plugins/docker-compose-buildkite-plugin
**Version documented:** v5.12.1

## Overview

Runs pipeline steps using Docker Compose for multi-container environments. Supports pre-building images for parallel builds, pushing to registries, and complex service orchestration.

## Configuration Options

### Primary Commands (one required)

| Option | Type | Description |
|--------|------|-------------|
| `run` | string | Service name to run commands in |
| `build` | string/array | Service(s) to build and store |
| `push` | array | Services to push to registry |

### Compose Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `config` | string/array | docker-compose.yml | Compose file(s) to use |
| `pull` | string/array | - | Pre-built images to pull before run |
| `skip-pull` | boolean | false | Skip all pull operations |
| `skip-checkout` | boolean | false | Skip repository checkout |

### Environment

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `environment` | array | - | Environment variables (`KEY` or `KEY=VALUE`) |
| `env-file` | string/array | - | Files to load as environment |
| `propagate-environment` | boolean | false | Pass all pipeline environment variables |
| `propagate-aws-auth-tokens` | boolean | false | Pass AWS authentication variables |
| `propagate-gcp-auth-tokens` | boolean | false | Pass GCP credentials |

### Container Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `workdir` | string | - | Working directory inside container |
| `user` | string | - | User to run as (uid or username) |
| `command` | array | - | Override container command |
| `shell` | array/boolean | ["/bin/sh", "-e", "-c"] | Shell for commands |
| `tty` | boolean | false | Allocate TTY |
| `propagate-uid-gid` | boolean | false | Match container UID/GID to host |

### Mounts and Volumes

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `mount-checkout` | boolean/string | false | Mount working directory |
| `mount-ssh-agent` | boolean/string | false | Mount SSH agent socket |
| `mount-buildkite-agent` | boolean | false | Mount buildkite-agent binary |
| `volumes` | array | - | Additional volume mounts |

### Build Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `args` | array | - | Build arguments (`KEY=VALUE`) |
| `target` | string | - | Dockerfile target stage |
| `no-cache` | boolean | false | Disable Docker cache |
| `build-parallel` | boolean | false | Build services in parallel |
| `cache-from` | array | - | Cache source images |
| `cache-to` | array | - | Cache export destinations |
| `buildkit-inline-cache` | boolean | false | Enable inline cache |

### Push Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `push-metadata` | boolean | true | Store image metadata for downstream |
| `push-retries` | integer | 0 | Number of push retry attempts |

### Service Dependencies

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `dependencies` | boolean | true | Start linked services |
| `pre-run-dependencies` | boolean | true | Start dependencies before container |
| `graceful-shutdown` | boolean | false | Graceful container termination |
| `leave-volumes` | boolean | false | Retain volumes after execution |

### Other

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `collapse-logs` | boolean | false | Collapse output in log groups |
| `pull-retries` | integer | 0 | Number of pull retry attempts |

## Examples

**Basic run:**
```yaml
steps:
  - command: "npm test"
    plugins:
      - docker-compose#v5.12.1:
          run: app
```

**Pre-build and run:**
```yaml
steps:
  - label: ":docker: Build"
    plugins:
      - docker-compose#v5.12.1:
          build: app
          push: app

  - wait

  - label: ":rspec: Test"
    plugins:
      - docker-compose#v5.12.1:
          run: app
          pull: app
```

**With environment and volumes:**
```yaml
steps:
  - command: "bundle exec rspec"
    plugins:
      - docker-compose#v5.12.1:
          run: app
          environment:
            - RAILS_ENV=test
            - DATABASE_URL
          mount-checkout: true
          volumes:
            - "./tmp/cache:/app/tmp/cache"
```

## Version-Specific Docs

For specific versions: https://github.com/buildkite-plugins/docker-compose-buildkite-plugin/tree/{version}
