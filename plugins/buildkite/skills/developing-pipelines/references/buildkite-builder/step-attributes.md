# Step Attributes

## Overview

All Buildkite step attributes are available in the buildkite-builder DSL. Attributes can be set within step blocks.

## Common Attributes

### label

Step display name:

```ruby
command do
  label "Run Tests"
  command "npm test"
end
```

### emoji

Add emoji to label (symbol or string):

```ruby
command do
  label "Test"
  emoji :test  # Symbol
  command "npm test"
end

command do
  label "Deploy"
  emoji ":rocket:"  # String
  command "./deploy.sh"
end
```

### key

Unique identifier for the step (used for dependencies):

```ruby
command do
  key "unit-tests"
  label "Unit Tests"
  command "npm test"
end
```

### command

Command(s) to execute (string, array, or heredoc):

```ruby
# String
command do
  label "Build"
  command "make build"
end

# Array
command do
  label "Setup"
  command [
    "npm install",
    "npm run build"
  ]
end

# Heredoc
command do
  label "Deploy"
  command <<~BASH
    echo "Starting deployment..."
    ./deploy.sh
  BASH
end
```

### condition

Conditional execution (replaces Buildkite's `if`):

```ruby
command do
  label "Deploy"
  command "./deploy.sh"
  condition "build.branch == 'main'"
end
```

### branches

Branch filter:

```ruby
command do
  label "Deploy"
  command "./deploy.sh"
  branches "main production"
end
```

### agents

Target specific agents:

```ruby
command do
  label "GPU Tests"
  command "python test_gpu.py"
  agents do
    queue "gpu"
  end
end
```

### retry

Retry configuration:

```ruby
command do
  label "Flaky Test"
  command "npm test"
  retry do
    automatic [
      { exit_status: "*", limit: 2 }
    ]
  end
end
```

### timeout_in_minutes

Step timeout:

```ruby
command do
  label "Long Test"
  command "npm run long-test"
  timeout_in_minutes 30
end
```

### parallelism

Run multiple instances in parallel:

```ruby
command do
  label "Parallel Tests"
  command "npm test -- --shard=\\$BUILDKITE_PARALLEL_JOB"
  parallelism 10
end
```

### concurrency & concurrency_group

Limit concurrent execution:

```ruby
command do
  label "Deploy"
  command "./deploy.sh"
  concurrency 1
  concurrency_group "deploy-production"
end
```

### soft_fail

Allow step to fail without failing build:

```ruby
command do
  label "Optional Check"
  command "npm run lint"
  soft_fail true
end
```

### skip

Skip step with reason:

```ruby
command do
  label "Deploy"
  command "./deploy.sh"
  skip "Not ready for deployment"
end
```

## Nested Blocks

Some attributes use nested blocks:

### agents

```ruby
agents do
  queue "default"
  os "linux"
end
```

### retry

```ruby
retry do
  automatic [
    { exit_status: -1, limit: 2 },
    { exit_status: 255, limit: 2 }
  ]
  manual do
    allowed true
    reason "Retry manually if needed"
  end
end
```

### build (for trigger steps)

```ruby
trigger do
  trigger "deploy-pipeline"
  build do
    message "Triggered deployment"
    branch "main"
    env do
      DEPLOY_ENV "production"
    end
  end
end
```

## Complete Example

```ruby
command do
  key "integration-tests"
  label "Integration Tests"
  emoji :test
  command "npm run test:integration"
  depends_on "unit-tests"
  condition "build.branch == 'main'"
  agents do
    queue "default"
  end
  retry do
    automatic [
      { exit_status: "*", limit: 2 }
    ]
  end
  timeout_in_minutes 20
  artifact_paths "coverage/**/*"
  env do
    NODE_ENV "test"
    API_URL "https://api.test.example.com"
  end
end
```
