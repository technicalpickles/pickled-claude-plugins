# buildkite-builder Support Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend the developing-buildkite-pipelines skill to support buildkite-builder Ruby DSL for dynamic pipeline generation.

**Architecture:** Add buildkite-builder detection to existing skill workflow, create 10 reference documentation files extracted from upstream README, and update skill to provide Ruby-first workflow with Docker-based validation.

**Tech Stack:** Markdown documentation, Ruby DSL reference, Docker validation commands

---

## Task 1: Create buildkite-builder Reference Directory Structure

**Files:**
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/index.md`
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/dsl-syntax.md`
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/step-attributes.md`
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/templates.md`
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/extensions.md`
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/conditionals.md`
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/dependencies.md`
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/artifacts.md`
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/plugins.md`
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/environment.md`

**Step 1: Create buildkite-builder directory**

Run: `mkdir -p plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder`
Expected: Directory created

**Step 2: Verify directory exists**

Run: `ls -la plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/ | grep buildkite-builder`
Expected: Directory listed

**Step 3: Commit directory creation**

```bash
git add plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/
git commit -m "feat: create buildkite-builder reference directory"
```

---

## Task 2: Write buildkite-builder/index.md

**Files:**
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/index.md`

**Step 1: Write index.md content**

Create file with overview, introduction, and when to use buildkite-builder vs YAML:

```markdown
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
```

**Step 2: Verify file created**

Run: `cat plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/index.md | head -n 5`
Expected: First 5 lines of file displayed

**Step 3: Commit index.md**

```bash
git add plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/index.md
git commit -m "feat: add buildkite-builder index reference doc"
```

---

## Task 3: Write buildkite-builder/dsl-syntax.md

**Files:**
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/dsl-syntax.md`

**Step 1: Write dsl-syntax.md content**

Create file with all step types and basic DSL syntax:

```markdown
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
```

**Step 2: Verify file created**

Run: `wc -l plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/dsl-syntax.md`
Expected: Line count displayed

**Step 3: Commit dsl-syntax.md**

```bash
git add plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/dsl-syntax.md
git commit -m "feat: add buildkite-builder DSL syntax reference"
```

---

## Task 4: Write buildkite-builder/step-attributes.md

**Files:**
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/step-attributes.md`

**Step 1: Write step-attributes.md content**

```markdown
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
```

**Step 2: Verify file created**

Run: `grep -c "^###" plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/step-attributes.md`
Expected: Count of attribute sections

**Step 3: Commit step-attributes.md**

```bash
git add plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/step-attributes.md
git commit -m "feat: add buildkite-builder step attributes reference"
```

---

## Task 5: Write buildkite-builder/templates.md

**Files:**
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/templates.md`

**Step 1: Write templates.md content**

```markdown
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
```

**Step 2: Verify file created**

Run: `grep -c "```ruby" plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/templates.md`
Expected: Count of Ruby code blocks

**Step 3: Commit templates.md**

```bash
git add plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/templates.md
git commit -m "feat: add buildkite-builder templates reference"
```

---

## Task 6: Write buildkite-builder/extensions.md

**Files:**
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/extensions.md`

**Step 1: Write extensions.md content**

```markdown
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
```

**Step 2: Verify file created**

Run: `head -n 20 plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/extensions.md`
Expected: First 20 lines displayed

**Step 3: Commit extensions.md**

```bash
git add plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/extensions.md
git commit -m "feat: add buildkite-builder extensions reference"
```

---

## Task 7: Write remaining reference files (conditionals, dependencies, artifacts, plugins, environment)

**Files:**
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/conditionals.md`
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/dependencies.md`
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/artifacts.md`
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/plugins.md`
- Create: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/environment.md`

**Step 1: Write conditionals.md**

```markdown
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
```

**Step 2: Write dependencies.md**

```markdown
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
```

**Step 3: Write artifacts.md**

```markdown
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
```

**Step 4: Write plugins.md**

```markdown
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
```

**Step 5: Write environment.md**

```markdown
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
```

**Step 6: Verify all files created**

Run: `ls -1 plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/`
Expected: All 10 files listed

**Step 7: Commit all remaining reference files**

```bash
git add plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/
git commit -m "feat: add buildkite-builder reference docs (conditionals, dependencies, artifacts, plugins, environment)"
```

---

## Task 8: Update SKILL.md with buildkite-builder Detection and Workflow

**Files:**
- Modify: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/SKILL.md`

**Step 1: Read current SKILL.md**

Run: `cat plugins/ci-cd-tools/skills/developing-buildkite-pipelines/SKILL.md`
Expected: Current skill content displayed

**Step 2: Add detection section after "The Iron Rule"**

Add new section after line 28 (after "## The Iron Rule"):

```markdown
## Detecting buildkite-builder

**Check for buildkite-builder usage before proceeding:**

buildkite-builder is detected when BOTH conditions are true:
1. `.buildkite/pipeline.yml` references Docker image containing "buildkite-builder"
2. Pipeline Ruby files exist: `.buildkite/pipeline.rb` OR `.buildkite/pipelines/*/pipeline.rb`

When detected, announce:

> "I see you're using buildkite-builder for dynamic pipeline generation. I'll work with your pipeline.rb files and reference the Ruby DSL."

Then load buildkite-builder reference documentation as needed.
```

**Step 3: Update "## Workflow" section**

Replace the current "### 1. Read Official Docs FIRST" section with:

```markdown
### 1. Detect buildkite-builder (if present)

Check for buildkite-builder usage:
- Docker image in `.buildkite/pipeline.yml` contains "buildkite-builder"
- `.buildkite/pipeline.rb` OR `.buildkite/pipelines/*/pipeline.rb` exists

If detected, announce and load buildkite-builder context.

### 2. Read Official Docs FIRST

**For YAML pipelines:**

Before writing or modifying pipeline YAML:

```markdown
**I need to reference the Buildkite documentation for [specific feature].**

Let me check: references/[relevant-doc].md
```

**For buildkite-builder pipelines:**

Before writing or modifying pipeline.rb:

```markdown
**I need to reference buildkite-builder documentation for [specific feature].**

Let me check: references/buildkite-builder/[relevant-doc].md
```
```

**Step 4: Update available references section**

After the existing references list (around line 50), add:

```markdown
**buildkite-builder references (when detected):**
- `buildkite-builder/index.md` - Overview and when to use
- `buildkite-builder/dsl-syntax.md` - Core DSL step types
- `buildkite-builder/step-attributes.md` - Common attributes
- `buildkite-builder/templates.md` - Reusable step templates
- `buildkite-builder/extensions.md` - Custom DSL and extensions
- `buildkite-builder/conditionals.md` - Conditional step generation
- `buildkite-builder/dependencies.md` - Step dependencies
- `buildkite-builder/artifacts.md` - Artifact handling
- `buildkite-builder/plugins.md` - Plugin usage in DSL
- `buildkite-builder/environment.md` - Environment variables

See `references/buildkite-builder/index.md` for complete guide.
```

**Step 5: Add buildkite-builder validation section**

After the existing "### 2. Validate Syntax" section, add:

```markdown
**For buildkite-builder pipelines:**

After proposing pipeline.rb changes:

1. Scan for ENV variable usage
2. Generate Docker validation command with placeholders
3. List detected environment variables

```bash
# Generate YAML locally
docker run --rm \
  -v $(pwd)/.buildkite:/workspace/.buildkite \
  -e BUILDKITE_BRANCH=main \
  -e BUILDKITE_COMMIT=abc123def \
  -e BUILDKITE_BUILD_NUMBER=1 \
  gusto/buildkite-builder:4.13.0

# Validate generated YAML
docker run ... | buildkite-agent pipeline upload --dry-run
```

Note: List any custom ENV variables found in pipeline.rb and suggest setting real values if needed.
```

**Step 6: Add troubleshooting mode section**

Before "## Common Mistakes", add new section:

```markdown
## buildkite-builder Troubleshooting Mode

When user mentions errors, "not generating", "YAML looks wrong", or validation failures with buildkite-builder:

1. **Read pipeline.rb** - Understand the Ruby DSL
2. **Run Docker command** - Generate YAML to see actual output
3. **Compare output** - Expected vs actual YAML
4. **Reference both docs** - buildkite-builder DSL AND Buildkite YAML docs
5. **Identify issue** - Where Ruby DSL produces unexpected YAML
6. **Propose fix** - Modify pipeline.rb to fix generation

This mode switches from Ruby-first to YAML-aware debugging.
```

**Step 7: Verify changes**

Run: `git diff plugins/ci-cd-tools/skills/developing-buildkite-pipelines/SKILL.md | head -n 50`
Expected: Diff showing new sections added

**Step 8: Commit SKILL.md updates**

```bash
git add plugins/ci-cd-tools/skills/developing-buildkite-pipelines/SKILL.md
git commit -m "feat: add buildkite-builder detection and workflow to skill"
```

---

## Task 9: Test buildkite-builder Detection Logic

**Files:**
- Test against example project structure

**Step 1: Create test directory structure**

Run: `mkdir -p .tmp/test-buildkite-builder/.buildkite/pipelines/test`
Expected: Directories created

**Step 2: Create test pipeline.yml with buildkite-builder**

Create `.tmp/test-buildkite-builder/.buildkite/pipeline.yml`:

```yaml
steps:
  - label: ":toolbox:"
    plugins:
      - docker#v5.12.0:
          image: "gusto/buildkite-builder:4.13.0"
```

**Step 3: Create test pipeline.rb**

Create `.tmp/test-buildkite-builder/.buildkite/pipelines/test/pipeline.rb`:

```ruby
Buildkite::Builder.pipeline do
  command do
    label "Test"
    command "echo 'Testing'"
  end
end
```

**Step 4: Test detection with grep**

Run: `grep -q "buildkite-builder" .tmp/test-buildkite-builder/.buildkite/pipeline.yml && echo "DETECTED"`
Expected: "DETECTED"

Run: `ls .tmp/test-buildkite-builder/.buildkite/pipelines/*/pipeline.rb && echo "FOUND"`
Expected: "FOUND"

**Step 5: Cleanup test directory**

Run: `rm -rf .tmp/test-buildkite-builder`
Expected: Directory removed

**Step 6: Document test results**

Create note in plan document that detection logic verified.

---

## Task 10: Final Validation and Documentation

**Files:**
- Verify all reference files exist and are accessible
- Update design document status

**Step 1: List all buildkite-builder references**

Run: `ls -1 plugins/ci-cd-tools/skills/developing-buildkite-pipelines/references/buildkite-builder/ | wc -l`
Expected: 10 files

**Step 2: Verify SKILL.md contains buildkite-builder sections**

Run: `grep -c "buildkite-builder" plugins/ci-cd-tools/skills/developing-buildkite-pipelines/SKILL.md`
Expected: Multiple occurrences (at least 10)

**Step 3: Check all commits**

Run: `git log --oneline --graph --decorate -n 10`
Expected: See all commits from this implementation

**Step 4: Update design document status**

Modify `docs/plans/2025-01-12-buildkite-builder-support-design.md` status from "Design" to "Implemented"

**Step 5: Commit design status update**

```bash
git add docs/plans/2025-01-12-buildkite-builder-support-design.md
git commit -m "docs: mark buildkite-builder design as implemented"
```

**Step 6: Create summary of changes**

Document summary:
- 10 reference files created in `references/buildkite-builder/`
- SKILL.md updated with detection and workflow
- All changes tested and committed

---

## Success Criteria

✅ Directory structure created with 10 reference files
✅ All reference files contain extracted buildkite-builder documentation
✅ SKILL.md updated with detection logic
✅ SKILL.md updated with buildkite-builder workflow
✅ SKILL.md updated with validation commands
✅ Detection logic tested and verified
✅ All changes committed to git
✅ Design document marked as implemented

## Next Steps (Post-Implementation)

1. Test skill with real buildkite-builder project
2. Refine reference documentation based on usage
3. Add more examples to reference files
4. Consider creating buildkite-builder templates showcase
