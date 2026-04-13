# Cache Buildkite Plugin

**Source:** https://github.com/buildkite-plugins/cache-buildkite-plugin
**Version documented:** v1.8.1

## Overview

Stores ephemeral cache files between builds. Preserves large datasets like downloaded packages, compiled caches, or VM images that remain relatively static across builds, improving build performance.

## Configuration Options

### Required

| Option | Type | Description |
|--------|------|-------------|
| `path` | string | File or folder to cache |
| `restore` | string | Max caching level to restore: `file`, `step`, `branch`, `pipeline`, `all` |
| `save` | string/array | Level(s) for saving cache |

**Note:** At least one of `restore` or `save` must be specified.

### Common Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `backend` | string | `fs` | Storage mechanism: `fs` or `s3` |
| `manifest` | string/array | - | File(s) to hash for cache invalidation (required for file-level) |
| `compression` | string | none | Compression format: `none`, `tgz`, `zip`, `zstd` |
| `force` | boolean | false | Force save even if cache exists |
| `soft-fail` | boolean | false | Continue build on cache operation failures |
| `key-extra` | string | - | Additional cache key differentiator |
| `keep-compressed-artifacts` | boolean | false | Keep temporary compressed files after use |

### Caching Levels

| Level | Scope |
|-------|-------|
| `file` | Valid only while manifest contents unchanged |
| `step` | Limited to current step execution |
| `branch` | Active during branch builds |
| `pipeline` | Shared across all pipeline builds |
| `all` | Always available (global) |

When restoring, checks all levels up to maximum specified, using first match.

### S3 Backend Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BUILDKITE_PLUGIN_S3_CACHE_BUCKET` | Yes | S3 bucket name |
| `BUILDKITE_PLUGIN_S3_CACHE_PREFIX` | No | Key prefix |
| `BUILDKITE_PLUGIN_S3_CACHE_ENDPOINT` | No | Custom endpoint |
| `BUILDKITE_PLUGIN_S3_CACHE_PROFILE` | No | AWS profile |

### Filesystem Backend Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BUILDKITE_PLUGIN_FS_CACHE_FOLDER` | `/var/cache/buildkite` | Cache directory |

## Examples

**Basic Node.js dependencies:**
```yaml
steps:
  - label: ":nodejs: Install"
    command: npm ci
    plugins:
      - cache#v1.8.1:
          manifest: package-lock.json
          path: node_modules
          restore: file
          save: file
```

**Multi-level caching strategy:**
```yaml
steps:
  - label: ":nodejs: Install"
    command: npm ci
    plugins:
      - cache#v1.8.1:
          manifest: package-lock.json
          path: node_modules
          restore: pipeline
          save:
            - file
            - branch
```

**S3 backend with compression:**
```yaml
env:
  BUILDKITE_PLUGIN_S3_CACHE_BUCKET: "my-cache-bucket"

steps:
  - label: ":nodejs: Install"
    command: npm ci
    plugins:
      - cache#v1.8.1:
          backend: s3
          manifest: package-lock.json
          path: node_modules
          restore: file
          save: file
          compression: zstd
```

**Non-critical caching with soft-fail:**
```yaml
steps:
  - label: ":nodejs: Install"
    command: npm ci
    plugins:
      - cache#v1.8.1:
          manifest: package-lock.json
          path: node_modules
          restore: file
          save: file
          soft-fail: true
```

## Version-Specific Docs

For specific versions: https://github.com/buildkite-plugins/cache-buildkite-plugin/tree/{version}
