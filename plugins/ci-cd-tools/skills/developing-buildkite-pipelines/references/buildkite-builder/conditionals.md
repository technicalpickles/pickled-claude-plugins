# Conditionals

## Overview

Use Ruby logic to conditionally generate pipeline steps based on branch, environment, code changes, or any other condition.

## Using Ruby Conditionals

Since buildkite-builder uses Ruby, you can use standard Ruby conditionals:

```ruby
Buildkite::Builder.pipeline do
  if ENV['BUILDKITE_BRANCH'] == 'main'
    command do
      label "Deploy to Production"
      command "./deploy.sh production"
    end
  end

  unless ENV['BUILDKITE_PULL_REQUEST'] == 'false'
    command do
      label "PR Checks"
      command "npm run lint"
    end
  end
end
```

## Buildkite's condition Attribute

Use the `condition` attribute for Buildkite-native conditionals:

```ruby
command do
  label "Deploy"
  command "./deploy.sh"
  condition "build.branch == 'main'"
end
```

**Note:** The DSL uses `condition` instead of `if` (Ruby keyword).

## Branch-Based Conditionals

```ruby
Buildkite::Builder.pipeline do
  command do
    label "Test"
    command "npm test"
  end

  if ENV['BUILDKITE_BRANCH'] == 'main'
    wait

    command do
      label "Deploy to Staging"
      command "./deploy.sh staging"
    end
  end

  if ENV['BUILDKITE_BRANCH'] =~ /^release\//
    wait

    command do
      label "Deploy to Production"
      command "./deploy.sh production"
    end
  end
end
```

## Pull Request Conditionals

```ruby
is_pr = ENV['BUILDKITE_PULL_REQUEST'] != 'false'

Buildkite::Builder.pipeline do
  if is_pr
    command do
      label "Lint"
      command "npm run lint"
    end

    command do
      label "Type Check"
      command "npm run type-check"
    end
  end

  command do
    label "Test"
    command "npm test"
  end
end
```

## File Change Detection

```ruby
def files_changed?(pattern)
  changed_files = `git diff --name-only HEAD^..HEAD`.split("\n")
  changed_files.any? { |file| file.match?(pattern) }
end

Buildkite::Builder.pipeline do
  if files_changed?(/^services\/api\//)
    command do
      label "Test API"
      command "cd services/api && npm test"
    end
  end

  if files_changed?(/^services\/web\//)
    command do
      label "Test Web"
      command "cd services/web && npm test"
    end
  end
end
```

## Environment-Based Conditionals

```ruby
deploy_env = ENV.fetch('DEPLOY_ENV', 'staging')

Buildkite::Builder.pipeline do
  command do
    label "Build"
    command "docker build -t app:${BUILDKITE_COMMIT} ."
  end

  wait

  case deploy_env
  when 'production'
    block do
      label "Approve Production Deploy"
    end

    wait

    command do
      label "Deploy to Production"
      command "./deploy.sh production"
    end
  when 'staging'
    command do
      label "Deploy to Staging"
      command "./deploy.sh staging"
    end
  else
    command do
      label "Deploy to Development"
      command "./deploy.sh development"
    end
  end
end
```

## Complex Conditional Logic

```ruby
def should_deploy?
  ENV['BUILDKITE_BRANCH'] == 'main' &&
    ENV['BUILDKITE_PULL_REQUEST'] == 'false' &&
    !ENV.fetch('SKIP_DEPLOY', '').empty?
end

def changed_services
  `git diff --name-only HEAD^..HEAD`
    .split("\n")
    .grep(/^services\//)
    .map { |path| path.split("/")[1] }
    .uniq
end

Buildkite::Builder.pipeline do
  # Test only changed services
  changed_services.each do |service|
    command do
      key "test-#{service}"
      label "Test #{service}"
      command "cd services/#{service} && npm test"
    end
  end

  # Deploy if conditions met
  if should_deploy?
    wait

    changed_services.each do |service|
      command do
        key "deploy-#{service}"
        label "Deploy #{service}"
        command "cd services/#{service} && ./deploy.sh"
        depends_on "test-#{service}"
      end
    end
  end
end
```

## Combining Ruby and Buildkite Conditionals

```ruby
Buildkite::Builder.pipeline do
  # Ruby conditional to decide whether to add step
  if ENV['BUILDKITE_BRANCH'] == 'main'
    command do
      label "Deploy"
      command "./deploy.sh"
      # Buildkite conditional for when step actually runs
      condition "build.env('DEPLOY_ENABLED') == 'true'"
    end
  end
end
```

## Best Practices

1. **Use Ruby for generation logic** - Decide which steps to add
2. **Use condition for runtime logic** - Decide when steps should run
3. **Extract logic into methods** - Keep pipeline definition clean
4. **Handle edge cases** - Check for nil/empty values
5. **Document complex conditionals** - Add comments explaining logic

## Common Patterns

**Skip deploy on PR:**
```ruby
is_pr = ENV['BUILDKITE_PULL_REQUEST'] != 'false'

unless is_pr
  command do
    label "Deploy"
    command "./deploy.sh"
  end
end
```

**Main branch only:**
```ruby
command do
  label "Deploy"
  command "./deploy.sh"
  branches "main"
end
```

**Specific file patterns:**
```ruby
if files_changed?(/\.(js|ts)x?$/)
  command do
    label "JavaScript Tests"
    command "npm test"
  end
end
```
