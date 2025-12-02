# Step Templates

## Overview

Templates allow you to extract reusable step definitions into separate files. This reduces duplication and makes pipelines easier to maintain.

## Template File Structure

```
.buildkite/
  pipelines/
    my-pipeline/
      pipeline.rb
      templates/
        rspec.rb
        rubocop.rb
        deploy.rb
```

## Creating a Template

Template files use `Buildkite::Builder.template` block:

`.buildkite/pipelines/my-pipeline/templates/rspec.rb`:

```ruby
Buildkite::Builder.template do
  label "Rspec"
  emoji :rspec
  command "bundle exec rspec"
end
```

## Using Templates

Reference templates by filename (without extension):

`.buildkite/pipelines/my-pipeline/pipeline.rb`:

```ruby
Buildkite::Builder.pipeline do
  command(:rspec)  # Uses templates/rspec.rb
end
```

## Augmenting Templates

Override or add attributes to templates:

```ruby
Buildkite::Builder.pipeline do
  # Use template as-is
  command(:rspec)

  # Override label
  command(:rspec) do
    label "Run RSpec Again!"
  end

  # Add dependencies
  command(:rspec) do
    depends_on "setup"
  end

  # Add environment variables
  command(:rspec) do
    env do
      RAILS_ENV "test"
    end
  end
end
```

## Template with Parameters

Templates can accept Ruby logic:

`.buildkite/pipelines/my-pipeline/templates/test.rb`:

```ruby
Buildkite::Builder.template do
  label "Test"
  emoji :test
  command "npm test"
end
```

Use multiple times with variations:

```ruby
Buildkite::Builder.pipeline do
  command(:test) do
    key "test-unit"
    label "Unit Tests"
    command "npm run test:unit"
  end

  command(:test) do
    key "test-integration"
    label "Integration Tests"
    command "npm run test:integration"
  end
end
```

## Multiple Templates in Sequence

```ruby
Buildkite::Builder.pipeline do
  command(:rubocop)
  command(:rspec)

  wait

  command(:deploy)
end
```

## Template Best Practices

1. **One template per file** - Keep templates focused
2. **Descriptive names** - Template filename should describe what it does
3. **Minimal defaults** - Set common defaults, allow overrides
4. **Reusable across pipelines** - Design templates to be pipeline-agnostic

## Complex Template Example

`.buildkite/pipelines/my-pipeline/templates/docker-build.rb`:

```ruby
Buildkite::Builder.template do
  label "Docker Build"
  emoji :docker
  command [
    "docker build -t app:${BUILDKITE_COMMIT} .",
    "docker tag app:${BUILDKITE_COMMIT} app:latest"
  ]
  agents do
    queue "docker"
  end
  retry do
    automatic [
      { exit_status: "*", limit: 2 }
    ]
  end
end
```

Usage:

```ruby
Buildkite::Builder.pipeline do
  command(:"docker-build") do
    key "build-web"
    label "Build Web Container"
    command "docker build -t web:${BUILDKITE_COMMIT} ./web"
  end

  command(:"docker-build") do
    key "build-api"
    label "Build API Container"
    command "docker build -t api:${BUILDKITE_COMMIT} ./api"
  end
end
```

## Template Location

Templates are scoped to their pipeline directory. If you need to share templates across multiple pipelines, consider using Extensions instead.
