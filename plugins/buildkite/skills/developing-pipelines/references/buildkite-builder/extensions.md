# Extensions

## Overview

Extensions provide additional flexibility to encapsulate reusable patterns across multiple pipelines. Extensions allow you to:
- Define custom DSL methods
- Create multiple related templates
- Share complex logic between pipelines

Think of extensions as Ruby modules that extend the pipeline DSL.

## Extension File Structure

```
.buildkite/
  pipelines/
    my-pipeline/
      pipeline.rb
      extensions/
        deploy_extension.rb
        test_extension.rb
```

## Creating an Extension

Extensions inherit from `Buildkite::Builder::Extension`:

`.buildkite/pipelines/my-pipeline/extensions/deploy_extension.rb`:

```ruby
class DeployExtension < Buildkite::Builder::Extension
  dsl do
    def deploy_step(&block)
      command(:deploy, &block)
    end
  end
end
```

## Using Extension DSL

`.buildkite/pipelines/my-pipeline/pipeline.rb`:

```ruby
Buildkite::Builder.pipeline do
  deploy_step do
    label "Deploy to Production (EU)"
    command "bundle exec deploy --env production --region eu"
  end

  deploy_step do
    label "Deploy to Production (US)"
    command "bundle exec deploy --env production --region us"
  end
end
```

## Extension Templates

Extensions can provide multiple templates:

`.buildkite/pipelines/my-pipeline/extensions/test_extension.rb`:

```ruby
class TestExtension < Buildkite::Builder::Extension
  template :default do
    label "RSpec"
    emoji :rspec
    command "bundle exec rspec"
  end

  template :rubocop do
    label "Rubocop"
    emoji :rubocop
    command "bundle exec rubocop"
  end

  template :integration do
    label "Integration Tests"
    emoji :test
    command "bundle exec rspec spec/integration"
  end
end
```

## Using Extension Templates

```ruby
Buildkite::Builder.pipeline do
  # Use default template
  command(TestExtension)

  # Use named template
  command(TestExtension.template(:rubocop))

  # Use and augment template
  command(TestExtension.template(:integration)) do
    depends_on "setup"
    agents do
      queue "integration"
    end
  end
end
```

## Complex Extension Example

`.buildkite/pipelines/my-pipeline/extensions/service_extension.rb`:

```ruby
class ServiceExtension < Buildkite::Builder::Extension
  dsl do
    def service_test(service_name, &block)
      command do
        key "test-#{service_name}"
        label "Test #{service_name.capitalize}"
        emoji :test
        command "cd services/#{service_name} && npm test"
        instance_eval(&block) if block_given?
      end
    end

    def service_build(service_name, &block)
      command do
        key "build-#{service_name}"
        label "Build #{service_name.capitalize}"
        emoji :docker
        command "docker build -t #{service_name}:${BUILDKITE_COMMIT} services/#{service_name}"
        depends_on "test-#{service_name}"
        instance_eval(&block) if block_given?
      end
    end
  end

  template :deploy do
    emoji :rocket
    command "echo 'Deploying...'"
  end
end
```

Usage:

```ruby
Buildkite::Builder.pipeline do
  service_test("api")
  service_test("web")
  service_test("worker")

  wait

  service_build("api")
  service_build("web")
  service_build("worker")

  wait

  command(ServiceExtension.template(:deploy)) do
    label "Deploy All Services"
    command "./deploy-all.sh"
  end
end
```

## Extension with Logic

Extensions can include complex logic:

```ruby
class ConditionalExtension < Buildkite::Builder::Extension
  dsl do
    def changed_services
      # Logic to detect changed services
      `git diff --name-only HEAD^..HEAD`
        .split("\n")
        .grep(/^services\//)
        .map { |path| path.split("/")[1] }
        .uniq
    end

    def test_changed_services
      changed_services.each do |service|
        command do
          key "test-#{service}"
          label "Test #{service}"
          command "cd services/#{service} && npm test"
        end
      end
    end
  end
end
```

Usage:

```ruby
Buildkite::Builder.pipeline do
  test_changed_services  # Only adds steps for changed services
end
```

## Extension Best Practices

1. **Single Responsibility** - Each extension should handle one area of concern
2. **Descriptive Names** - Name extensions after what they do (DeployExtension, TestExtension)
3. **Document DSL methods** - Add comments explaining custom DSL methods
4. **Combine DSL + Templates** - Use DSL for logic, templates for reusable steps
5. **Keep extensions pipeline-agnostic** - Design to work across multiple pipelines

## Extensions vs Templates

**Use Templates when:**
- You have a simple, reusable step definition
- No custom logic needed
- Scoped to a single pipeline

**Use Extensions when:**
- You need custom DSL methods
- Multiple related templates
- Complex logic or analysis
- Sharing across multiple pipelines
