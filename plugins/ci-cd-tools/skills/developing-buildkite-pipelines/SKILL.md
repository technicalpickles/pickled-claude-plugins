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

## Detecting buildkite-builder

**Check for buildkite-builder usage before proceeding:**

buildkite-builder is detected when BOTH conditions are true:
1. `.buildkite/pipeline.yml` references Docker image containing "buildkite-builder"
2. Pipeline Ruby files exist: `.buildkite/pipeline.rb` OR `.buildkite/pipelines/*/pipeline.rb`

When detected, announce:

> "I see you're using buildkite-builder for dynamic pipeline generation. I'll work with your pipeline.rb files and reference the Ruby DSL."

Then load buildkite-builder reference documentation as needed.

## Workflow

### 1. Detect buildkite-builder (if present)

Check for buildkite-builder usage:
- Docker image in `.buildkite/pipeline.yml` contains "buildkite-builder"
- `.buildkite/pipeline.rb` OR `.buildkite/pipelines/*/pipeline.rb` exists

If detected, announce and load buildkite-builder context.

### 2. Read Official Docs FIRST

**For YAML pipelines:**

Before writing or modifying pipeline YAML:

```markdown
**I need to reference the Buildkite documentation for [specific feature].**

Let me check: @references/[relevant-doc].md
```

**For buildkite-builder pipelines:**

Before writing or modifying pipeline.rb:

```markdown
**I need to reference buildkite-builder documentation for [specific feature].**

Let me check: @references/buildkite-builder/[relevant-doc].md
```

**Available references:**
- `step-types.md` - Command, trigger, block, wait, input steps
- `dynamic-pipelines.md` - Generating steps programmatically
- `dependencies.md` - Using depends_on, parallel steps
- `environment-variables.md` - Setting and using env vars
- `conditionals.md` - if/branches for conditional execution
- `artifacts.md` - Uploading and downloading build artifacts

See `@references/index.md` for complete list.

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

See `@references/buildkite-builder/index.md` for complete guide.

### 3. Validate Syntax

After proposing changes, ALWAYS mention validation:

```bash
# Validate locally before pushing
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

### 4. Check for Official Plugins

Before writing custom scripts, check if a Buildkite plugin exists:

```markdown
**Before implementing custom Docker builds, check:**
- docker-buildkite-plugin
- ecr-buildkite-plugin
- docker-compose-buildkite-plugin

Official plugins at: https://buildkite.com/plugins
```

## buildkite-builder Troubleshooting Mode

When user mentions errors, "not generating", "YAML looks wrong", or validation failures with buildkite-builder:

1. **Read pipeline.rb** - Understand the Ruby DSL
2. **Run Docker command** - Generate YAML to see actual output
3. **Compare output** - Expected vs actual YAML
4. **Reference both docs** - buildkite-builder DSL AND Buildkite YAML docs
5. **Identify issue** - Where Ruby DSL produces unexpected YAML
6. **Propose fix** - Modify pipeline.rb to fix generation

This mode switches from Ruby-first to YAML-aware debugging.

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
