# Artifacts Buildkite Plugin

**Source:** https://github.com/buildkite-plugins/artifacts-buildkite-plugin
**Version documented:** v1.9.4

## Overview

Uploads and downloads build artifacts within Buildkite pipelines. Allows artifact dependencies to be resolved before step execution, ideal for multi-job workflows where one job produces artifacts needed by subsequent jobs.

## Configuration Options

### Required (at least one)

| Option | Type | Description |
|--------|------|-------------|
| `upload` | string/array/object | Glob pattern(s) or `{from, to}` for files to upload |
| `download` | string/array/object | Glob pattern(s) or `{from, to}` for files to download |

### Download Options

| Option | Type | Description |
|--------|------|-------------|
| `build` | string | Build UUID for artifact source |
| `step` | string | Job UUID or step key for artifact source |

### Upload Options

| Option | Type | Description |
|--------|------|-------------|
| `skip-on-status` | integer/array | Exit codes that skip upload |
| `s3-upload-acl` | string | S3 object-level ACL (e.g., `public-read`) |
| `gs-upload-acl` | string | Google Cloud Storage ACL |

### Common Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `compressed` | string | - | Archive filename (`.zip` or `.tgz`) for compression |
| `ignore-missing` | boolean | false | Suppress errors when artifacts unavailable |
| `expand-upload-vars` | boolean | false | Enable variable interpolation in upload paths (unsafe) |
| `expand-download-vars` | boolean | false | Enable variable interpolation in download paths (unsafe) |

## Examples

**Simple upload:**
```yaml
steps:
  - command: "npm test"
    plugins:
      - artifacts#v1.9.4:
          upload: "coverage/**/*"
```

**Download from specific step:**
```yaml
steps:
  - command: "./deploy.sh"
    plugins:
      - artifacts#v1.9.4:
          download: "dist/*"
          step: "build"
```

**Rename during upload/download:**
```yaml
steps:
  - command: "npm run build"
    plugins:
      - artifacts#v1.9.4:
          upload:
            - from: build/output.zip
              to: release.zip
```

**Cross-build artifact retrieval:**
```yaml
steps:
  - command: "./compare.sh"
    plugins:
      - artifacts#v1.9.4:
          download:
            - from: results.json
              build: "${BASELINE_BUILD_ID}"
```

## Version-Specific Docs

For specific versions: https://github.com/buildkite-plugins/artifacts-buildkite-plugin/tree/{version}
