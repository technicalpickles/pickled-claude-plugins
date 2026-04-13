# buildkite-builder DSL Syntax

## Overview

The buildkite-builder DSL matches Buildkite's step types and attributes. If it exists in Buildkite docs, it exists in the DSL.

**Exception:** The `if` attribute is called `condition` (since `if` is a Ruby keyword).

## Basic Pipeline Structure

```ruby
Buildkite::Builder.pipeline do
  # Steps go here
end
```

## Step Types

### Command Steps

Execute commands in the pipeline:

```ruby
command do
  label "Test"
  emoji :test
  command "bundle exec rspec"
end
```

**Single-line command:**

```ruby
command do
  label "Build"
  command "make build"
end
```

**Multi-line command:**

```ruby
command do
  label "Deploy"
  command <<~BASH
    echo "Deploying..."
    ./deploy.sh
  BASH
end
```

**Array of commands:**

```ruby
command do
  label "Setup and Test"
  command [
    "bundle install",
    "bundle exec rspec"
  ]
end
```

### Wait Steps

Pause the pipeline until all previous steps complete:

```ruby
wait
```

**Wait with continue_on_failure:**

```ruby
wait do
  continue_on_failure true
end
```

### Trigger Steps

Trigger another pipeline:

```ruby
trigger do
  trigger "deploy-pipeline"
end
```

**With build metadata:**

```ruby
trigger do
  trigger "deploy-pipeline"
  build do
    message "Deploy from main branch"
    branch "main"
  end
end
```

### Block Steps

Pause for manual unblock:

```ruby
block do
  label "Deploy to Production?"
end
```

**With prompt:**

```ruby
block do
  label "Approve Deployment"
  prompt "Are you sure you want to deploy?"
end
```

### Input Steps

Collect user input:

```ruby
input do
  label "Deployment Details"
  prompt "Enter deployment information"
  fields [
    { key: "environment", text: "Environment" },
    { key: "version", text: "Version" }
  ]
end
```

## Multiple Steps

```ruby
Buildkite::Builder.pipeline do
  command do
    label "Lint"
    command "bundle exec rubocop"
  end

  command do
    label "Test"
    command "bundle exec rspec"
  end

  wait

  command do
    label "Build"
    command "docker build -t app ."
  end
end
```

## Using Templates

Reference step templates by name:

```ruby
Buildkite::Builder.pipeline do
  command(:rspec)  # Uses templates/rspec.rb

  # Augment template
  command(:rspec) do
    label "Run RSpec Again!"
  end
end
```

## DSL Reference

All Buildkite step attributes are available in the DSL:
- `label` - Step name
- `emoji` - Emoji for step (symbol like `:test` or string like `":rocket:"`)
- `command` - Command(s) to run
- `trigger` - Pipeline to trigger
- `block` - Block step configuration
- `input` - Input step configuration
- `key` - Unique step identifier
- `depends_on` - Step dependencies (see dependencies.md)
- `condition` - Conditional execution (instead of `if`)
- `branches` - Branch filter
- `agents` - Agent targeting
- `artifact_paths` - Artifacts to upload (see artifacts.md)
- `plugins` - Buildkite plugins (see plugins.md)
- `env` - Environment variables (see environment.md)
- `retry` - Retry configuration
- `timeout_in_minutes` - Step timeout
- `parallelism` - Parallel job count
- `concurrency` - Concurrency limit
- `concurrency_group` - Concurrency group name

See Buildkite documentation for complete attribute reference.
