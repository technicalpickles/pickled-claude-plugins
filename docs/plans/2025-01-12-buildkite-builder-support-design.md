# buildkite-builder Support for developing-buildkite-pipelines Skill

**Date**: 2025-01-12
**Status**: Design

## Problem

The `developing-buildkite-pipelines` skill helps users work with Buildkite pipeline YAML files. However, many projects use [buildkite-builder](https://github.com/Gusto/buildkite-builder), a Ruby DSL that generates pipeline YAML dynamically. The skill needs to support this workflow.

## Goals

1. Detect when buildkite-builder is in use
2. Help users write and modify `pipeline.rb` files using the Ruby DSL
3. Provide validation commands that generate YAML locally via Docker
4. Support troubleshooting when generated YAML doesn't match expectations

## Non-Goals

- Teaching Ruby programming fundamentals
- Supporting buildkite-builder development/contributing
- Replacing the existing YAML-focused workflow

## Detection Strategy

The skill detects buildkite-builder when **both** conditions are true:

1. `.buildkite/pipeline.yml` references a Docker image containing "buildkite-builder"
2. Pipeline Ruby files exist in either:
   - `.buildkite/pipeline.rb`, OR
   - `.buildkite/pipelines/*/pipeline.rb`

When detected, the skill announces:

> "I see you're using buildkite-builder for dynamic pipeline generation. I'll work with your pipeline.rb files and reference the Ruby DSL."

## Workflow Modes

### Normal Mode: Ruby-First

Used for standard pipeline modifications:

1. Read relevant `pipeline.rb` file(s)
2. Reference `references/buildkite-builder/*` documentation
3. Propose changes in Ruby DSL
4. Provide Docker validation command with environment variables

### Troubleshooting Mode: YAML-Aware

Triggered when user mentions errors, "not generating", "YAML looks wrong", or validation failures:

1. Read `pipeline.rb` (Ruby source)
2. Run Docker command to generate YAML
3. Compare expected output vs actual output
4. Reference both buildkite-builder DSL docs AND core Buildkite YAML docs
5. Identify where Ruby DSL produces unexpected YAML
6. Propose fix in `pipeline.rb`

## Reference Documentation Structure

New directory: `references/buildkite-builder/`

**Files**:
- `index.md` - Overview, when to use builder vs raw YAML
- `dsl-syntax.md` - Core DSL: command, wait, trigger, block, input steps
- `step-attributes.md` - Common attributes: label, emoji, key, depends_on
- `templates.md` - Template system for reusable step definitions
- `extensions.md` - Custom extensions for shared logic
- `conditionals.md` - Conditional step generation with Ruby logic
- `dependencies.md` - depends_on in DSL, parallel steps
- `artifacts.md` - artifact_paths in DSL
- `plugins.md` - Using Buildkite plugins in the DSL
- `environment.md` - ENV variable access, setting env in DSL

**Content Source**: Extract from Gusto/buildkite-builder README, optimized for LLM consumption. Remove contributing/development sections.

## Validation Approach

### Docker-Based Validation

After proposing `pipeline.rb` changes, generate a validation command:

1. Scan `pipeline.rb` for `ENV['...']` or `ENV.fetch('...')` patterns
2. Generate Docker command with safe placeholder values
3. List detected environment variables and their defaults

**Example**:

```bash
docker run --rm \
  -v $(pwd)/.buildkite:/workspace/.buildkite \
  -e BUILDKITE_BRANCH=main \
  -e BUILDKITE_COMMIT=abc123def \
  -e BUILDKITE_BUILD_NUMBER=1 \
  -e CUSTOM_VAR=placeholder \
  gusto/buildkite-builder:4.13.0
```

**Output to user**:

> Your pipeline.rb references: ENV['CUSTOM_VAR']
> Set real values if placeholders don't work for your logic.

### Environment Variable Handling

- **Detect**: Parse `pipeline.rb` for ENV access patterns
- **Provide defaults**: Common Buildkite vars get realistic placeholders
- **Flag custom vars**: Explicitly list which custom vars need real values
- **Document pattern**: Show how to add `-e` or `--env-file` for additional vars

### Validation Output Usage

```bash
# Save generated YAML
docker run ... > generated.yml

# Validate with buildkite-agent
docker run ... | buildkite-agent pipeline upload --dry-run

# Inspect for correctness
docker run ... | less
```

## Integration with Existing Skill

### Skill Workflow Update

```markdown
## Workflow

### 1. Detect buildkite-builder (if present)

Check for buildkite-builder usage:
- Docker image in .buildkite/pipeline.yml contains "buildkite-builder"
- .buildkite/pipeline.rb OR .buildkite/pipelines/*/pipeline.rb exists

If detected, announce and load buildkite-builder context.

### 2. Read Official Docs FIRST

**For YAML pipelines:**
Before writing or modifying pipeline YAML...

**For buildkite-builder pipelines:**
Before writing or modifying pipeline.rb:

```markdown
**I need to reference buildkite-builder documentation for [specific feature].**

Let me check: references/buildkite-builder/[relevant-doc].md
```

[Rest of existing workflow continues...]
```

### Updated References Section

Add to "Available references":

```markdown
**buildkite-builder references:**
- `buildkite-builder/index.md` - Overview and when to use
- `buildkite-builder/dsl-syntax.md` - Core DSL step types
- `buildkite-builder/templates.md` - Reusable step templates
- `buildkite-builder/extensions.md` - Custom extensions

See `references/buildkite-builder/index.md` for complete list.
```

## Implementation Plan

1. Create `references/buildkite-builder/` directory structure
2. Extract and optimize content from buildkite-builder README
3. Write 10 reference files covering all user-facing features
4. Update `SKILL.md` with detection logic
5. Add buildkite-builder workflow section
6. Update validation section with Docker approach
7. Add buildkite-builder examples to skill
8. Test with real buildkite-builder projects

## Success Criteria

- Skill correctly detects buildkite-builder usage
- Proposes valid Ruby DSL modifications
- Provides working Docker validation commands
- Detects and lists environment variables
- Can troubleshoot YAML generation issues
- References accurate buildkite-builder documentation
