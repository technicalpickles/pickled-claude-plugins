# buildkite-builder Overview

## Introduction

Buildkite Builder (BKB) is a Ruby DSL for dynamically generating Buildkite pipeline steps. It allows you to build your pipeline programmatically with Ruby for complex, dynamic pipeline generation.

## When to Use buildkite-builder vs Raw YAML

**Use buildkite-builder when:**
- You need conditional step generation based on code changes
- Your pipeline requires complex logic (loops, conditionals, analysis)
- You want to reuse step definitions across multiple pipelines
- You need to perform pre-build code analysis
- Your pipeline has many similar steps that can be templated

**Use raw YAML when:**
- Your pipeline is simple and static
- You don't need dynamic step generation
- You want maximum simplicity and transparency

## How It Works

1. **Initial pipeline.yml** calls buildkite-builder Docker image
2. **pipeline.rb** contains Ruby DSL that generates steps
3. **Docker image** executes the Ruby code and outputs YAML
4. **Generated YAML** is uploaded to Buildkite

## Pipeline Installation

In `.buildkite/pipeline.yml`:

```yaml
steps:
  - label: ":toolbox:"
    key: "buildkite-builder"
    plugins:
      - docker#v5.12.0:
          image: "gusto/buildkite-builder:4.13.0"
          mount-buildkite-agent: true
          propagate-environment: true
```

## Pipeline File Structure

```
.buildkite/
  pipeline.rb              # Single pipeline
  # OR
  pipelines/
    <pipeline-slug>/
      pipeline.rb          # Multiple pipelines
      templates/
        step-name.rb
      extensions/
        extension-name.rb
```

## Basic Example

`.buildkite/pipeline.rb`:

```ruby
Buildkite::Builder.pipeline do
  command do
    label "Rspec", emoji: :rspec
    command "bundle exec rspec"
  end

  wait

  trigger do
    trigger "deploy-pipeline"
  end
end
```

Generates:

```yaml
steps:
  - label: ":rspec: RSpec"
    command: "bundle exec rspec"
  - wait
  - trigger: deploy-pipeline
```

## Reference Files

- `dsl-syntax.md` - Core DSL for all step types
- `step-attributes.md` - Common attributes (label, emoji, key, depends_on)
- `templates.md` - Reusable step templates
- `extensions.md` - Custom DSL and shared logic
- `conditionals.md` - Conditional step generation with Ruby
- `dependencies.md` - Step dependencies and parallel execution
- `artifacts.md` - Artifact handling in DSL
- `plugins.md` - Using Buildkite plugins in DSL
- `environment.md` - Environment variable access and manipulation

## Key Features

- **Dynamic step generation** - Use Ruby logic to create steps
- **Pre-build analysis** - Analyze code/diffs before generating steps
- **Step reordering** - Dynamically change step order
- **Templates** - Extract reusable step definitions
- **Extensions** - Create custom DSL and shared logic
