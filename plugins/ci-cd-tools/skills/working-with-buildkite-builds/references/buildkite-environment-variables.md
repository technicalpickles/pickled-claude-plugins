# Buildkite Environment Variables Reference

This reference documents the standard environment variables that Buildkite sets during build execution. Understanding these variables is essential for reproducing CI failures locally.

> **Source:** Based on official Buildkite documentation at https://buildkite.com/docs/pipelines/configure/environment-variables

## Purpose

When reproducing a build failure locally, you often need to set environment variables that CI sets automatically. This reference helps you identify:

- Which variables CI sets that your code might depend on
- What values to use when running commands locally
- Which variables are informational vs. behavior-changing

## Categories

### Core CI Detection Variables

These are the most commonly checked variables that control behavior in CI vs. local environments.

| Variable | Value in CI | Purpose | Set Locally? |
|----------|-------------|---------|--------------|
| `CI` | `true` | Universal CI indicator | Yes - use `CI=true` |
| `BUILDKITE` | `true` | Buildkite-specific indicator | Yes - use `BUILDKITE=true` |

**Local reproduction pattern:**
```bash
CI=true BUILDKITE=true <your-command>
```

### Build Identification Variables

These identify the build context but rarely affect local behavior.

| Variable | Example Value | Purpose | Set Locally? |
|----------|---------------|---------|--------------|
| `BUILDKITE_BUILD_ID` | `f62a1b4d-10f9-4790-bc1c-e2c3a0c80983` | Unique build identifier | No - informational only |
| `BUILDKITE_BUILD_NUMBER` | `1514` | Sequential build number | No - informational only |
| `BUILDKITE_BUILD_URL` | `https://buildkite.com/org/pipeline/builds/1514` | URL to build | No - informational only |
| `BUILDKITE_BUILD_CREATOR` | `jane@example.com` | User who triggered build | Rarely |
| `BUILDKITE_BUILD_CREATOR_EMAIL` | `jane@example.com` | Creator's email | Rarely |
| `BUILDKITE_REBUILT_FROM_BUILD_ID` | `uuid` | Original build ID if rebuild | No |
| `BUILDKITE_REBUILT_FROM_BUILD_NUMBER` | `1513` | Original build number if rebuild | No |

**When to set locally:** Only if your code explicitly checks these (e.g., reporting build number in logs).

### Source Control Variables

These describe the git context of the build.

| Variable | Example Value | Purpose | Set Locally? |
|----------|---------------|---------|--------------|
| `BUILDKITE_BRANCH` | `main` or `feature/new-thing` | Branch being built | Sometimes |
| `BUILDKITE_COMMIT` | `83a20ec058e2fb00e7fa4558c4c6e81e2dcf253d` | Git commit SHA | Sometimes |
| `BUILDKITE_TAG` | `v1.2.3` | Git tag if build triggered by tag | Sometimes |
| `BUILDKITE_MESSAGE` | `Fix user authentication bug` | Commit message | Rarely |
| `BUILDKITE_REPO` | `git@github.com:org/repo.git` | Repository URL | Rarely |
| `BUILDKITE_PULL_REQUEST` | `123` or `false` | PR number or false if not PR | Yes - if testing PR-specific behavior |
| `BUILDKITE_PULL_REQUEST_BASE_BRANCH` | `main` | Target branch for PR | Yes - if testing PR merges |
| `BUILDKITE_PULL_REQUEST_REPO` | `git://github.com/org/repo.git` | PR repository URL | Rarely |

**Local reproduction patterns:**

For branch-specific behavior:
```bash
BUILDKITE_BRANCH=main <your-command>
```

For PR-specific behavior:
```bash
BUILDKITE_PULL_REQUEST=123 BUILDKITE_PULL_REQUEST_BASE_BRANCH=main <your-command>
```

For commit-specific behavior:
```bash
BUILDKITE_COMMIT=$(git rev-parse HEAD) <your-command>
```

### Job Context Variables

These describe the specific job within a build.

| Variable | Example Value | Purpose | Set Locally? |
|----------|---------------|---------|--------------|
| `BUILDKITE_JOB_ID` | `e44f9784-e20e-4b93-a21d-f41fd5869db9` | Unique job identifier | No |
| `BUILDKITE_STEP_ID` | `abc123` | Step ID from pipeline | Rarely |
| `BUILDKITE_STEP_KEY` | `tests` | Step key from pipeline | Sometimes |
| `BUILDKITE_LABEL` | `🧪 Unit Tests` | Job label shown in UI | No |
| `BUILDKITE_COMMAND` | `bin/rspec` | Command being executed | No - you're running it |
| `BUILDKITE_PARALLEL_JOB` | `2` | Index of parallel job (0-based) | Yes - if reproducing parallel failure |
| `BUILDKITE_PARALLEL_JOB_COUNT` | `5` | Total parallel jobs | Yes - if reproducing parallel failure |

**Local reproduction patterns:**

For parallel job issues:
```bash
BUILDKITE_PARALLEL_JOB=2 BUILDKITE_PARALLEL_JOB_COUNT=5 <your-command>
```

For step-key-dependent behavior:
```bash
BUILDKITE_STEP_KEY=tests <your-command>
```

### Agent Variables

These describe the agent running the job. Rarely needed locally.

| Variable | Example Value | Purpose | Set Locally? |
|----------|---------------|---------|--------------|
| `BUILDKITE_AGENT_ID` | `uuid` | Unique agent identifier | No |
| `BUILDKITE_AGENT_NAME` | `ci-agent-1` | Agent name | No |
| `BUILDKITE_AGENT_META_DATA_*` | varies | Agent metadata/tags | Rarely |

**When to set locally:** Only if code routes behavior based on agent metadata.

### Pipeline Variables

These describe the pipeline configuration.

| Variable | Example Value | Purpose | Set Locally? |
|----------|---------------|---------|--------------|
| `BUILDKITE_PIPELINE_ID` | `uuid` | Pipeline identifier | No |
| `BUILDKITE_PIPELINE_SLUG` | `my-app` | Pipeline URL slug | Rarely |
| `BUILDKITE_PIPELINE_NAME` | `My App` | Pipeline display name | No |
| `BUILDKITE_PIPELINE_PROVIDER` | `github` | Source control provider | Rarely |
| `BUILDKITE_ORGANIZATION_SLUG` | `my-org` | Organization URL slug | Rarely |

### Artifact and Directory Variables

These relate to Buildkite-specific features.

| Variable | Example Value | Purpose | Set Locally? |
|----------|---------------|---------|--------------|
| `BUILDKITE_ARTIFACT_PATHS` | `coverage/**/*` | Artifact upload patterns | No - use local paths |
| `BUILDKITE_BUILD_CHECKOUT_PATH` | `/buildkite/builds/...` | Checkout directory | No - use your local path |
| `BUILDKITE_BUILD_PATH` | `/buildkite/builds` | Builds directory | No |
| `BUILDKITE_BIN_PATH` | `/usr/local/bin` | Agent bin path | No |
| `BUILDKITE_HOOKS_PATH` | `/buildkite/hooks` | Hooks directory | No |
| `BUILDKITE_PLUGINS_PATH` | `/buildkite/plugins` | Plugins directory | No |

### Timing Variables

Available during and after build execution.

| Variable | Example Value | Purpose | Set Locally? |
|----------|---------------|---------|--------------|
| `BUILDKITE_TIMEOUT` | `false` or seconds | Job timeout | No |
| `BUILDKITE_COMMAND_EXIT_STATUS` | `1` | Exit code of command | No - you'll see it |

## Common Local Reproduction Scenarios

### Scenario 1: Basic test failure

**Minimal reproduction:**
```bash
CI=true <test-command>
```

Most test suites only check `CI` to enable CI-specific behavior.

### Scenario 2: Branch-specific logic

**Example:** Different database seeding on main vs. feature branches

```bash
CI=true BUILDKITE_BRANCH=$(git branch --show-current) <command>
```

### Scenario 3: PR-specific checks

**Example:** Linters that only check changed files in PRs

```bash
CI=true BUILDKITE_PULL_REQUEST=123 BUILDKITE_PULL_REQUEST_BASE_BRANCH=main <command>
```

### Scenario 4: Parallel test failure

**Example:** Tests fail only in specific parallel partition

```bash
CI=true BUILDKITE_PARALLEL_JOB=2 BUILDKITE_PARALLEL_JOB_COUNT=5 <test-command>
```

### Scenario 5: Full CI environment simulation

**When reproducing complex CI-specific behavior:**

```bash
CI=true \
BUILDKITE=true \
BUILDKITE_BRANCH=$(git branch --show-current) \
BUILDKITE_COMMIT=$(git rev-parse HEAD) \
BUILDKITE_BUILD_NUMBER=local \
<command>
```

## How to Discover Which Variables Matter

### Method 1: Check the logs

Look for environment variable dumps early in CI logs:
```
--- Environment
CI=true
BUILDKITE=true
BUILDKITE_BRANCH=main
...
```

### Method 2: Check pipeline configuration

Look in `.buildkite/pipeline.yml` or buildkite-builder DSL for `env:` blocks:

```yaml
steps:
  - label: "Tests"
    command: "bin/rspec"
    env:
      RAILS_ENV: test
      DATABASE_URL: postgres://localhost/test
```

### Method 3: Search the codebase

Search for environment variable usage:

```bash
# Search for BUILDKITE variable usage
rg "ENV\[.BUILDKITE" --type ruby
rg "process\.env\.BUILDKITE" --type js
rg "os\.getenv\(.BUILDKITE" --type python
```

### Method 4: Progressive discovery

Start with minimal variables and add more if behavior differs:

1. Try: `CI=true <command>`
2. If different: Add `BUILDKITE=true`
3. If still different: Add `BUILDKITE_BRANCH=...`
4. Continue until behavior matches

## Variables to Avoid Setting Locally

**Don't set these unless absolutely necessary:**

- `BUILDKITE_AGENT_*` - Agent-specific, not relevant to command execution
- `BUILDKITE_BUILD_ID` / `BUILDKITE_BUILD_NUMBER` - Informational, shouldn't affect logic
- `BUILDKITE_BUILD_PATH` - Use your local paths instead
- `BUILDKITE_ARTIFACT_PATHS` - Artifacts are CI orchestration concern

If your code depends on these, it may be a code smell indicating too much CI-specific logic in your application.

## Best Practices

### For local reproduction

1. **Start minimal**: Begin with `CI=true` and add variables only as needed
2. **Use real values**: Set `BUILDKITE_BRANCH` to your actual branch name, not fake values
3. **Document assumptions**: Note which env vars you set when reporting issues
4. **Clean up**: Don't leave CI variables set in your shell permanently

### For application code

1. **Prefer `CI` over `BUILDKITE`**: Makes code portable across CI systems
2. **Use feature flags over env vars**: Don't branch behavior on `BUILDKITE_BRANCH` in app code
3. **Document dependencies**: If code checks env vars, document why in comments
4. **Minimize CI-specific logic**: The less your code knows about CI, the easier it is to test

## Related References

- **[troubleshooting.md](troubleshooting.md)** - Common issues when env vars are missing or incorrect
- **[SKILL.md](../SKILL.md)** - See "Reproducing Build Failures Locally" workflow for how to use this reference
