# Environment Variables

## Overview

Access and set environment variables in buildkite-builder pipelines using Ruby's `ENV` object and the `env` step attribute.

## Reading Environment Variables

Use Ruby's `ENV` to access environment variables:

```ruby
branch = ENV['BUILDKITE_BRANCH']
is_pr = ENV['BUILDKITE_PULL_REQUEST'] != 'false'
commit = ENV['BUILDKITE_COMMIT']

Buildkite::Builder.pipeline do
  command do
    label "Deploy to #{branch}"
    command "./deploy.sh #{branch}"
  end
end
```

## Common Buildkite Environment Variables

```ruby
ENV['BUILDKITE_BRANCH']                    # Branch name
ENV['BUILDKITE_COMMIT']                    # Commit SHA
ENV['BUILDKITE_BUILD_NUMBER']              # Build number
ENV['BUILDKITE_PULL_REQUEST']              # PR number or "false"
ENV['BUILDKITE_PULL_REQUEST_BASE_BRANCH']  # PR base branch
ENV['BUILDKITE_TAG']                       # Git tag
ENV['BUILDKITE_MESSAGE']                   # Commit message
```

Full list: https://buildkite.com/docs/pipelines/environment-variables

## Setting Environment Variables in Steps

Use the `env` block to set variables for a step:

```ruby
command do
  label "Test"
  command "npm test"
  env do
    NODE_ENV "test"
    API_URL "https://api.test.example.com"
  end
end
```

## Multiple Environment Variables

```ruby
command do
  label "Deploy"
  command "./deploy.sh"
  env do
    DEPLOY_ENV "production"
    DEPLOY_REGION "us-east-1"
    DEPLOY_VERSION ENV['BUILDKITE_COMMIT']
  end
end
```

## ENV.fetch with Defaults

Provide default values for missing variables:

```ruby
deploy_env = ENV.fetch('DEPLOY_ENV', 'staging')
timeout = ENV.fetch('BUILD_TIMEOUT', '30').to_i

Buildkite::Builder.pipeline do
  command do
    label "Deploy to #{deploy_env}"
    command "./deploy.sh #{deploy_env}"
    timeout_in_minutes timeout
  end
end
```

## Conditional Logic with ENV

```ruby
if ENV['BUILDKITE_BRANCH'] == 'main'
  command do
    label "Deploy to Production"
    command "./deploy.sh production"
    env do
      DEPLOY_ENV "production"
    end
  end
else
  command do
    label "Deploy to Staging"
    command "./deploy.sh staging"
    env do
      DEPLOY_ENV "staging"
    end
  end
end
```

## Docker Validation with ENV

When validating pipelines locally with Docker, pass required environment variables:

```bash
docker run --rm \
  -v $(pwd)/.buildkite:/workspace/.buildkite \
  -e BUILDKITE_BRANCH=main \
  -e BUILDKITE_COMMIT=abc123 \
  -e BUILDKITE_BUILD_NUMBER=1 \
  -e CUSTOM_VAR=value \
  gusto/buildkite-builder:4.13.0
```

## Environment Variables in Extensions

```ruby
class DeployExtension < Buildkite::Builder::Extension
  dsl do
    def deploy_to_env(env_name)
      command do
        label "Deploy to #{env_name}"
        command "./deploy.sh"
        env do
          DEPLOY_ENV env_name
          DEPLOY_COMMIT ENV['BUILDKITE_COMMIT']
          DEPLOY_BRANCH ENV['BUILDKITE_BRANCH']
        end
      end
    end
  end
end

Buildkite::Builder.pipeline do
  if ENV['BUILDKITE_BRANCH'] == 'main'
    deploy_to_env('production')
  else
    deploy_to_env('staging')
  end
end
```

## Complete Example

```ruby
# Read environment
branch = ENV['BUILDKITE_BRANCH']
is_main = branch == 'main'
is_pr = ENV['BUILDKITE_PULL_REQUEST'] != 'false'
commit = ENV.fetch('BUILDKITE_COMMIT', 'unknown')

Buildkite::Builder.pipeline do
  command do
    label "Test"
    command "npm test"
    env do
      NODE_ENV "test"
      CI "true"
    end
  end

  if is_pr
    command do
      label "PR Checks"
      command "npm run lint"
      env do
        PR_NUMBER ENV['BUILDKITE_PULL_REQUEST']
      end
    end
  end

  if is_main
    wait

    command do
      label "Deploy to Production"
      command "./deploy.sh"
      env do
        DEPLOY_ENV "production"
        DEPLOY_COMMIT commit
        DEPLOY_BRANCH branch
      end
    end
  end
end
```

## Best Practices

1. **Use ENV.fetch for required vars** - Fail fast if missing
2. **Provide defaults** - Use ENV.fetch(key, default) for optional vars
3. **Document custom vars** - Comment required environment variables
4. **Test with Docker** - Validate locally with all required env vars
5. **Don't hardcode secrets** - Use Buildkite's secret management
