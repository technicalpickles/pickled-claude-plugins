# Plugins

## Overview

Buildkite plugins can be used in buildkite-builder pipelines. The `plugins` attribute accepts an array of plugin configurations.

## Basic Plugin Usage

```ruby
command do
  label "Docker Build"
  command "echo 'Building...'"
  plugins [
    {
      "docker#v5.12.0" => {
        "image" => "node:20"
      }
    }
  ]
end
```

## Multiple Plugins

```ruby
command do
  label "Build and Push"
  command "make build"
  plugins [
    {
      "docker#v5.12.0" => {
        "image" => "node:20",
        "workdir" => "/app"
      }
    },
    {
      "artifacts#v1.9.3" => {
        "upload" => "dist/**/*"
      }
    }
  ]
end
```

## Common Plugins

### Docker Plugin

```ruby
plugins [
  {
    "docker#v5.12.0" => {
      "image" => "node:20",
      "workdir" => "/app",
      "environment" => ["NODE_ENV=production"],
      "volumes" => ["/cache:/cache"]
    }
  }
]
```

### Docker Compose Plugin

```ruby
plugins [
  {
    "docker-compose#v5.2.0" => {
      "run" => "app",
      "config" => "docker-compose.test.yml"
    }
  }
]
```

### Artifacts Plugin

```ruby
plugins [
  {
    "artifacts#v1.9.3" => {
      "upload" => "build/**/*",
      "download" => "dependencies/**/*"
    }
  }
]
```

### ECR Plugin

```ruby
plugins [
  {
    "ecr#v2.7.0" => {
      "login" => true,
      "account_ids" => "123456789",
      "region" => "us-east-1"
    }
  },
  {
    "docker#v5.12.0" => {
      "image" => "123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:latest"
    }
  }
]
```

## Plugin Version Management with Extensions

Reuse plugin versions across multiple steps:

```ruby
class DockerExtension < Buildkite::Builder::Extension
  DOCKER_VERSION = "v5.12.0"
  NODE_IMAGE = "node:20"

  dsl do
    def docker_command(image: NODE_IMAGE, &block)
      command do
        plugins [
          {
            "docker##{DOCKER_VERSION}" => {
              "image" => image
            }
          }
        ]
        instance_eval(&block) if block_given?
      end
    end
  end
end

Buildkite::Builder.pipeline do
  docker_command do
    label "Test"
    command "npm test"
  end

  docker_command(image: "node:18") do
    label "Test on Node 18"
    command "npm test"
  end
end
```

## Plugin Configuration Blocks

For complex plugin configs, use heredoc:

```ruby
docker_compose_config = {
  "docker-compose#v5.2.0" => {
    "run" => "app",
    "config" => ["docker-compose.yml", "docker-compose.test.yml"],
    "env" => ["NODE_ENV=test"],
    "volumes" => [
      "./:/app",
      "/tmp/cache:/cache"
    ]
  }
}

command do
  label "Integration Test"
  command "npm run test:integration"
  plugins [docker_compose_config]
end
```

## Complete Example

```ruby
Buildkite::Builder.pipeline do
  command do
    label "Lint"
    command "npm run lint"
    plugins [
      {
        "docker#v5.12.0" => {
          "image" => "node:20",
          "workdir" => "/app"
        }
      }
    ]
  end

  command do
    label "Test"
    command "npm test"
    plugins [
      {
        "docker#v5.12.0" => {
          "image" => "node:20",
          "workdir" => "/app",
          "environment" => ["NODE_ENV=test"]
        }
      },
      {
        "artifacts#v1.9.3" => {
          "upload" => "coverage/**/*"
        }
      }
    ]
  end

  wait

  command do
    label "Build"
    command "npm run build"
    plugins [
      {
        "docker#v5.12.0" => {
          "image" => "node:20",
          "workdir" => "/app"
        }
      },
      {
        "artifacts#v1.9.3" => {
          "upload" => "dist/**/*"
        }
      }
    ]
  end
end
```

## Finding Plugins

Official Buildkite plugins: https://buildkite.com/plugins

Most common plugins:
- `docker` - Run steps in Docker containers
- `docker-compose` - Run steps with Docker Compose
- `artifacts` - Advanced artifact handling
- `ecr` - Amazon ECR authentication
- `cache` - Dependency caching
