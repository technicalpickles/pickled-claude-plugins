# Dependencies

## Overview

Use the `depends_on` attribute to create dependencies between steps. This controls step execution order and enables parallel execution where possible.

## Basic Dependencies

```ruby
Buildkite::Builder.pipeline do
  command do
    key "build"
    label "Build"
    command "npm run build"
  end

  command do
    key "test"
    label "Test"
    command "npm test"
    depends_on "build"
  end
end
```

## Multiple Dependencies

```ruby
command do
  key "deploy"
  label "Deploy"
  command "./deploy.sh"
  depends_on ["test-unit", "test-integration", "lint"]
end
```

## Parallel Execution

Steps without dependencies run in parallel:

```ruby
Buildkite::Builder.pipeline do
  command do
    key "test-unit"
    label "Unit Tests"
    command "npm run test:unit"
  end

  command do
    key "test-integration"
    label "Integration Tests"
    command "npm run test:integration"
  end

  command do
    key "lint"
    label "Lint"
    command "npm run lint"
  end

  # Wait for all parallel steps
  wait

  command do
    key "deploy"
    label "Deploy"
    command "./deploy.sh"
  end
end
```

## Step Keys

Dependencies reference steps by their `key`:

```ruby
command do
  key "setup"
  label "Setup"
  command "npm install"
end

command do
  key "build"
  label "Build"
  command "npm run build"
  depends_on "setup"
end

command do
  key "test"
  label "Test"
  command "npm test"
  depends_on ["setup", "build"]
end
```

## Dependency Chains

```ruby
Buildkite::Builder.pipeline do
  command do
    key "lint"
    label "Lint"
    command "npm run lint"
  end

  command do
    key "build"
    label "Build"
    command "npm run build"
    depends_on "lint"
  end

  command do
    key "test"
    label "Test"
    command "npm test"
    depends_on "build"
  end

  command do
    key "deploy"
    label "Deploy"
    command "./deploy.sh"
    depends_on "test"
  end
end
```

## Parallel with Dependencies

```ruby
Buildkite::Builder.pipeline do
  command do
    key "setup"
    label "Setup"
    command "npm install"
  end

  # These run in parallel after setup
  command do
    key "test-unit"
    label "Unit Tests"
    command "npm run test:unit"
    depends_on "setup"
  end

  command do
    key "test-integration"
    label "Integration Tests"
    command "npm run test:integration"
    depends_on "setup"
  end

  command do
    key "lint"
    label "Lint"
    command "npm run lint"
    depends_on "setup"
  end

  # Waits for all three parallel steps
  command do
    key "deploy"
    label "Deploy"
    command "./deploy.sh"
    depends_on ["test-unit", "test-integration", "lint"]
  end
end
```

## Dynamic Dependencies

Generate dependencies programmatically:

```ruby
services = ['api', 'web', 'worker']

Buildkite::Builder.pipeline do
  # Create test step for each service
  test_keys = services.map do |service|
    key = "test-#{service}"
    command do
      key key
      label "Test #{service}"
      command "cd services/#{service} && npm test"
    end
    key
  end

  wait

  # Deploy depends on all tests
  command do
    key "deploy"
    label "Deploy All"
    command "./deploy-all.sh"
    depends_on test_keys
  end
end
```

## Wait Steps

Use `wait` to ensure all previous steps complete:

```ruby
Buildkite::Builder.pipeline do
  command do
    label "Test 1"
    command "npm test"
  end

  command do
    label "Test 2"
    command "npm test"
  end

  # Wait for both tests
  wait

  command do
    label "Deploy"
    command "./deploy.sh"
  end
end
```

## Continue on Failure

Wait can continue even if previous steps fail:

```ruby
wait do
  continue_on_failure true
end
```

## Best Practices

1. **Always use keys for dependencies** - Don't rely on step order
2. **Maximize parallelism** - Only add necessary dependencies
3. **Use wait for clarity** - Makes pipeline flow obvious
4. **Group related steps** - Use dependencies to create logical groups
5. **Avoid circular dependencies** - Buildkite will reject invalid graphs
