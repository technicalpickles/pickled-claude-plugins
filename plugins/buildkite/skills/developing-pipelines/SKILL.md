---
name: developing-pipelines
description: Use when creating, modifying, or debugging Buildkite pipeline YAML files - ensures current syntax from official docs, validates configurations before proposing changes, and references Buildkite best practices instead of relying on training data
---

# Developing Buildkite Pipelines

## Overview

Read the matching file under `references/` before writing or changing pipeline YAML or `pipeline.rb`. Training data lags Buildkite's current syntax, plugin options, and deprecations.

## Working with Plugins

### Before Modifying Plugin Configuration

When editing pipeline steps that use plugins:

1. **Identify plugins** - Note all `plugins:` entries in the step
2. **Determine source:**
   - Default org `buildkite-plugins` if no org specified
   - Parse explicit org from `{org}/{plugin}#version` format
3. **Load documentation:**
   - **Cached:** Check [references/plugins/{plugin-name}.md](references/plugins/)
   - **Official (not cached):** Fetch from Buildkite directory or GitHub
   - **Internal:** Fetch README from `github.com/{org}/{plugin}-buildkite-plugin`
4. **Match versions** - If pipeline specifies version, fetch that version's docs from GitHub tag

### Fetching Plugin Documentation

**Buildkite directory (latest):**
```
https://buildkite.com/resources/plugins/{org}/{plugin-name}-buildkite-plugin
```

**GitHub README (version-specific):**
```
https://github.com/{org}/{plugin-name}-buildkite-plugin/tree/{version}
```

### Plugin Discovery

**"Is there a plugin for X?"**

1. Check [references/plugins/index.md](references/plugins/index.md) for common plugins by category
2. Fetch Buildkite directory: `https://buildkite.com/resources/plugins/`
3. Search by task type (caching, docker, secrets, etc.)

**Internal plugins:**

Search org's GitHub for repos matching `*-buildkite-plugin`

## Workflow

### 1. Detect buildkite-builder (if present)

buildkite-builder generates the pipeline from Ruby. It is in use when both hold:
- `.buildkite/pipeline.yml` references a Docker image containing "buildkite-builder"
- `.buildkite/pipeline.rb` or `.buildkite/pipelines/*/pipeline.rb` exists

When it is, edit the `pipeline.rb` files and read [references/buildkite-builder/](references/buildkite-builder/index.md) alongside the YAML references.

### 2. Read the reference first

Before writing the change, read the matching file in [references/](references/index.md) for YAML, or in [references/buildkite-builder/](references/buildkite-builder/index.md) for `pipeline.rb`.

**Available references:**
- `step-types.md` - Command, trigger, block, wait, input steps
- `dynamic-pipelines.md` - Generating steps programmatically
- `dependencies.md` - Using depends_on, parallel steps
- `environment-variables.md` - Setting and using env vars
- `conditionals.md` - if/branches for conditional execution
- `artifacts.md` - Uploading and downloading build artifacts

See [references/index.md](references/index.md) for complete list.

**Plugin references (see [references/plugins/index.md](references/plugins/index.md) for full list):**
- `plugins/docker.md` - Docker container execution
- `plugins/docker-compose.md` - Multi-container environments
- `plugins/artifacts.md` - Artifact upload/download
- `plugins/ecr.md` - AWS ECR authentication
- `plugins/cache.md` - Dependency caching

**buildkite-builder references (when detected):**
- `buildkite-builder/index.md` - Overview and when to use
- `buildkite-builder/dsl-syntax.md` - Core DSL step types
- `buildkite-builder/step-attributes.md` - Common attributes
- `buildkite-builder/templates.md` - Reusable step templates
- `buildkite-builder/extensions.md` - Custom DSL and extensions
- `buildkite-builder/conditionals.md` - Conditional step generation
- `buildkite-builder/dependencies.md` - Step dependencies
- `buildkite-builder/artifacts.md` - Artifact handling
- `buildkite-builder/plugins.md` - Plugin usage in DSL
- `buildkite-builder/environment.md` - Environment variables

See [references/buildkite-builder/index.md](references/buildkite-builder/index.md) for complete guide.

### 3. Validate Syntax

Validate before proposing the change. When no validator is installed, give the user the command instead.

```bash
# Schema check with the bk CLI, local, no API token
bk pipeline validate --file .buildkite/pipeline.yml

# Or with buildkite-agent, where it is installed
buildkite-agent pipeline upload --dry-run < pipeline.yml

# Or validate a generated pipeline
./generate-pipeline.sh | buildkite-agent pipeline upload --dry-run
```

**For buildkite-builder pipelines:**

After proposing pipeline.rb changes:

1. Scan for ENV variable usage
2. Generate Docker validation command with placeholders
3. List detected environment variables

```bash
# Generate YAML locally
docker run --rm \
  -v $(pwd)/.buildkite:/workspace/.buildkite \
  -e BUILDKITE_BRANCH=main \
  -e BUILDKITE_COMMIT=abc123def \
  -e BUILDKITE_BUILD_NUMBER=1 \
  gusto/buildkite-builder:4.13.0

# Validate generated YAML
docker run ... | buildkite-agent pipeline upload --dry-run
```

Note: List any custom ENV variables found in pipeline.rb and suggest setting real values if needed.

### 4. Load Plugin Documentation

For any step with a `plugins:` block, follow [Working with Plugins](#working-with-plugins) before changing it.

## buildkite-builder Troubleshooting Mode

When user mentions errors, "not generating", "YAML looks wrong", or validation failures with buildkite-builder:

1. **Read pipeline.rb** - Understand the Ruby DSL
2. **Run Docker command** - Generate YAML to see actual output
3. **Compare output** - Expected vs actual YAML
4. **Reference both docs** - buildkite-builder DSL AND Buildkite YAML docs
5. **Identify issue** - Where Ruby DSL produces unexpected YAML
6. **Propose fix** - Modify pipeline.rb to fix generation

This mode switches from Ruby-first to YAML-aware debugging.

## Dynamic Pipelines Pattern

When generating steps programmatically:

1. **Reference dynamic-pipelines.md** for current patterns
2. **Use Buildkite SDK** if available (see dynamic-pipelines.md)
3. **Validate generated output** with --dry-run
4. **Consider official examples** before custom implementations

```bash
# Standard pattern from official docs
.buildkite/pipeline.sh | buildkite-agent pipeline upload
```

## Debugging Configuration Errors

When pipeline fails with validation errors:

1. **Verify step structure** in references/step-types.md
2. **Validate dependencies** in references/dependencies.md
3. **Don't speculate** - look up the actual validation rules
