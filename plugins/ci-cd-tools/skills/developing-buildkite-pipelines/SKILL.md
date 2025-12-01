---
name: developing-buildkite-pipelines
description: Use when creating, modifying, or debugging Buildkite pipeline YAML files - ensures current syntax from official docs, validates configurations before proposing changes, and references Buildkite best practices instead of relying on training data
---

# Developing Buildkite Pipelines

## Overview

**Reference official Buildkite documentation before making pipeline changes.** Your training data may contain outdated syntax, deprecated patterns, or missing features.

## When to Use

Use this skill when:
- Writing or modifying pipeline.yml files
- Creating dynamic pipelines
- Debugging pipeline configuration errors
- Adding new step types (command, trigger, block, wait)
- Configuring dependencies, artifacts, or parallelism
- Setting up Buildkite plugins

Do NOT use for:
- Checking build status (use buildkite-status skill)
- General CI/CD concepts (language-agnostic advice)

## The Iron Rule

**NEVER propose Buildkite YAML without consulting the reference docs.**

## Workflow

### 1. Read Official Docs FIRST

Before writing or modifying pipeline YAML:

```markdown
**I need to reference the Buildkite documentation for [specific feature].**

Let me check: @references/[relevant-doc].md
```

**Available references:**
- `step-types.md` - Command, trigger, block, wait, input steps
- `dynamic-pipelines.md` - Generating steps programmatically
- `dependencies.md` - Using depends_on, parallel steps
- `environment-variables.md` - Setting and using env vars
- `conditionals.md` - if/branches for conditional execution
- `artifacts.md` - Uploading and downloading build artifacts

See `@references/index.md` for complete list.

### 2. Validate Syntax

After proposing changes, ALWAYS mention validation:

```bash
# Validate locally before pushing
buildkite-agent pipeline upload --dry-run < pipeline.yml

# Or validate a generated pipeline
./generate-pipeline.sh | buildkite-agent pipeline upload --dry-run
```

### 3. Check for Official Plugins

Before writing custom scripts, check if a Buildkite plugin exists:

```markdown
**Before implementing custom Docker builds, check:**
- docker-buildkite-plugin
- ecr-buildkite-plugin
- docker-compose-buildkite-plugin

Official plugins at: https://buildkite.com/plugins
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Writing YAML from memory | Read step-types.md first |
| "This should work..." | Validate with --dry-run |
| Custom script without checking plugins | Search buildkite.com/plugins |
| Speculating about errors | Check references/troubleshooting.md |
| Assuming syntax from training data | Verify against current docs |

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

1. **Check error message** against references/troubleshooting.md
2. **Verify step structure** in references/step-types.md
3. **Validate dependencies** in references/dependencies.md
4. **Don't speculate** - look up the actual validation rules

## Red Flags - You're About to Violate

- "Based on my knowledge of Buildkite..."
- "This syntax should work..."
- "The validator likely fails because..."
- "Let me create a dynamic pipeline..." (without reading docs)
- Writing YAML before reading references
- Confident statements about Buildkite behavior without verification

**All of these mean: STOP. Read the docs first.**

## Real-World Impact

**Without this skill:**
- Agent wrote 2,600-line dynamic pipeline from memory (Scenario 2 baseline)
- Agent speculated about validator behavior without verification (Scenario 3 baseline)
- Agent assumed syntax patterns without checking current docs

**With this skill:**
- Reference official patterns and current syntax
- Validate before proposing
- Avoid outdated or deprecated approaches
