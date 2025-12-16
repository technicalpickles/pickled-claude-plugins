# Buildkite Plugin Knowledge Extension

**Date:** 2025-12-16
**Status:** Approved
**Extends:** `ci-cd-tools/skills/developing-buildkite-pipelines`

## Problem

When modifying pipeline steps that use Buildkite plugins, the skill lacks accurate configuration reference. Users must manually look up plugin docs. This leads to:
- Guessing at configuration options
- Using outdated syntax from training data
- Missing version-specific differences

## Solution

Extend `developing-buildkite-pipelines` with:
1. Pre-cached reference docs for common plugins
2. Workflow for fetching docs on demand (public and internal plugins)
3. Version-aware documentation lookup

## When It Activates

- Modifying a pipeline step that uses plugins
- Adding a new plugin to a step
- Debugging plugin-related errors
- Discovering what plugins exist for a task

## Reference Structure

```
plugins/ci-cd-tools/skills/developing-buildkite-pipelines/
├── SKILL.md (updated)
├── references/
│   ├── ... (existing docs)
│   └── plugins/
│       ├── index.md           # Plugin discovery & lookup guide
│       ├── docker.md          # Cached: docker plugin
│       ├── docker-compose.md  # Cached: docker-compose plugin
│       ├── artifacts.md       # Cached: artifacts plugin
│       ├── ecr.md             # Cached: ECR plugin
│       └── cache.md           # Cached: cache plugin
```

### `references/plugins/index.md`

Contains:
- Lookup workflow (URL patterns for directory and GitHub)
- Common plugins table (name, org, purpose, cached status)
- Category hints ("For caching: cache, s3-cache. For Docker: docker, docker-compose, ecr")

### Cached Plugin Doc Format

```markdown
# {Plugin Name} Plugin

**GitHub:** https://github.com/{org}/{plugin}-buildkite-plugin
**Version documented:** vX.Y.Z
**Last updated:** YYYY-MM-DD

## Overview
[Brief description]

## Configuration Options
[All options with types, defaults, descriptions]

## Common Examples
[2-3 usage patterns]

## Version-Specific Docs
For other versions: https://github.com/{org}/{plugin}-buildkite-plugin/tree/{version}
```

## Pre-cached Plugins

| Plugin | Org | Purpose |
|--------|-----|---------|
| docker | buildkite-plugins | Run steps in containers |
| docker-compose | buildkite-plugins | Multi-container test environments |
| artifacts | buildkite-plugins | Upload/download build artifacts |
| ecr | buildkite-plugins | AWS ECR authentication |
| cache | gantry | Dependency caching |

## SKILL.md Workflow Updates

### New Section: "Working with Plugins"

```markdown
## Working with Plugins

### Before Modifying Plugin Configuration

When editing pipeline steps that use plugins:

1. **Identify plugins** - Note all `plugins:` entries in the step
2. **Determine source** - Is it `buildkite-plugins/X` (official) or `{other-org}/X` (custom)?
3. **Load docs:**
   - Cached: `@references/plugins/{plugin-name}.md`
   - Official: Fetch from Buildkite directory or GitHub
   - Internal: Fetch README from `github.com/{org}/{plugin}-buildkite-plugin`
4. **Match versions** - If pipeline specifies a version, fetch that version's docs

### Fetching Plugin Documentation

**Buildkite directory (latest):**
```
https://buildkite.com/resources/plugins/{org}/{plugin-name}-buildkite-plugin
```

**GitHub README (version-specific):**
```
https://github.com/{org}/{plugin-name}-buildkite-plugin/tree/{version}
```

Most official plugins use org `buildkite-plugins`.

### Plugin Discovery

**Public plugins:**
1. Check `@references/plugins/index.md` for common plugins by category
2. Fetch directory: `https://buildkite.com/resources/plugins/`

**Internal plugins:**
1. Search org's GitHub for repos matching `*-buildkite-plugin`
2. Check the repo's README for configuration docs
```

### Update to Existing Workflow

Add checkpoint before "Validate Syntax": "If step uses plugins, load plugin docs first."

## Version Parsing

From YAML:
```yaml
plugins:
  - docker-compose#v5.12.1:
      run: app
```
Extract: plugin=`docker-compose`, org=`buildkite-plugins` (default), version=`v5.12.1`

From:
```yaml
plugins:
  - seek-oss/docker-ecr-cache#v2.2.0:
      ...
```
Extract: plugin=`docker-ecr-cache`, org=`seek-oss`, version=`v2.2.0`

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Plugin not in cache, fetch fails | Note failure, suggest checking GitHub directly, proceed with caution |
| Version tag doesn't exist | Fall back to latest/HEAD docs, warn about version mismatch |
| Non-standard org | Parse org from plugin reference |
| Plugin has no README | Use Buildkite directory page as fallback |
| Multiple plugins in one step | Load docs for all before making changes |

## Implementation Tasks

1. Create `references/plugins/index.md` with lookup workflow and plugin table
2. Fetch and format cached docs for 5 core plugins
3. Update SKILL.md with "Working with Plugins" section
4. Add plugin checkpoint to existing workflow
