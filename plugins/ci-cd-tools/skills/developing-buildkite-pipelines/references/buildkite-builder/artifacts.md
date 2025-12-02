# Artifacts

## Overview

Use `artifact_paths` to upload build artifacts that can be downloaded by later steps or viewed in the Buildkite UI.

## Basic Artifact Upload

```ruby
command do
  label "Build"
  command "npm run build"
  artifact_paths "dist/**/*"
end
```

## Multiple Artifact Patterns

```ruby
command do
  label "Build and Test"
  command [
    "npm run build",
    "npm test"
  ]
  artifact_paths [
    "dist/**/*",
    "coverage/**/*",
    "logs/*.log"
  ]
end
```

## Artifact Glob Patterns

```ruby
# All files in directory
artifact_paths "build/**/*"

# Specific file types
artifact_paths "dist/**/*.js"

# Multiple patterns
artifact_paths [
  "dist/**/*.js",
  "dist/**/*.css",
  "dist/**/*.html"
]

# Top-level files only
artifact_paths "*.zip"
```

## Downloading Artifacts

Buildkite automatically downloads artifacts from previous steps:

```ruby
Buildkite::Builder.pipeline do
  command do
    key "build"
    label "Build"
    command "npm run build"
    artifact_paths "dist/**/*"
  end

  command do
    key "deploy"
    label "Deploy"
    command "./deploy.sh"
    depends_on "build"
    # Artifacts from "build" step available in working directory
  end
end
```

## Using Buildkite Plugins

For more control over artifacts, use the artifacts plugin:

```ruby
command do
  label "Build"
  command "npm run build"
  plugins [
    {
      "artifacts#v1.9.3" => {
        "upload" => "dist/**/*",
        "download" => "dependencies/**/*"
      }
    }
  ]
end
```

## Artifact Best Practices

1. **Be specific with patterns** - Avoid uploading unnecessary files
2. **Use compression** - Zip large artifacts before uploading
3. **Set retention policies** - Configure artifact retention in Buildkite
4. **Download only what's needed** - Use specific artifact patterns

## Common Patterns

**Build artifacts:**
```ruby
artifact_paths "dist/**/*"
```

**Test coverage:**
```ruby
artifact_paths "coverage/**/*"
```

**Logs:**
```ruby
artifact_paths [
  "logs/*.log",
  "*.log"
]
```

**Docker images (as tarballs):**
```ruby
command do
  label "Build Docker Image"
  command [
    "docker build -t app:${BUILDKITE_COMMIT} .",
    "docker save app:${BUILDKITE_COMMIT} | gzip > app.tar.gz"
  ]
  artifact_paths "app.tar.gz"
end
```

## Complete Example

```ruby
Buildkite::Builder.pipeline do
  command do
    key "build"
    label "Build"
    command "npm run build"
    artifact_paths "dist/**/*"
  end

  command do
    key "test"
    label "Test"
    command "npm test"
    artifact_paths "coverage/**/*"
  end

  wait

  command do
    key "deploy"
    label "Deploy"
    command "./deploy.sh"
    depends_on ["build", "test"]
    # dist/ and coverage/ artifacts available here
  end
end
```
