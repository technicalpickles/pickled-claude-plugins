# Buildkite Pipeline Configuration Reference

Official Buildkite documentation for pipeline configuration, converted to markdown.

**Last updated:** Run `./update-docs.sh` to refresh from buildkite.com

## Core Pipeline Configuration

| File | Purpose |
|------|---------|
| `defining-steps.md` | Overview of how to define pipeline steps |
| `step-types.md` | Command, trigger, block, wait, input, group steps |
| `dependencies.md` | Using `depends_on` for step dependencies |
| `conditionals.md` | Conditional execution with `if` field |
| `environment-variables.md` | Setting and using environment variables |

## Dynamic Pipelines

| File | Purpose |
|------|---------|
| `dynamic-pipelines.md` | Generating pipeline steps programmatically |
| `example-pipelines.md` | Real-world pipeline examples |

## Build Artifacts & Data

| File | Purpose |
|------|---------|
| `artifacts.md` | Uploading and downloading build artifacts |
| `build-meta-data.md` | Storing metadata for builds |

## Advanced Features

| File | Purpose |
|------|---------|
| `glob-pattern-syntax.md` | Glob patterns for artifacts and file matching |
| `writing-build-scripts.md` | Best practices for build scripts |
| `notifications.md` | Configuring build notifications |
| `build-timeouts.md` | Setting timeouts for steps and builds |
| `tags.md` | Organizing pipelines with tags |
| `skipping.md` | Skipping builds based on conditions |

## Workflows

| File | Purpose |
|------|---------|
| `workflows/branch-configuration.md` | Branch filtering and configuration |
| `workflows/build-matrix.md` | Matrix builds for multiple configurations |
| `workflows/controlling-concurrency.md` | Limiting concurrent builds |
| `workflows/managing-priorities.md` | Build queue priorities |
| `workflows/scheduled-builds.md` | Cron-style scheduled builds |

## Pipeline Management

| File | Purpose |
|------|---------|
| `public-pipelines.md` | Making pipelines publicly visible |
| `build-retention.md` | Build history retention policies |
| `job-minutes.md` | Tracking and limiting job minutes |
| `workflows/archiving-and-deleting-pipelines.md` | Pipeline lifecycle management |

## Output & Logging

| File | Purpose |
|------|---------|
| `managing-log-output.md` | Controlling log verbosity and output |
| `links-and-images-in-log-output.md` | Rich log formatting |

## Quick Lookup

**Adding steps?** → `step-types.md`
**Dynamic pipelines?** → `dynamic-pipelines.md`
**Step dependencies?** → `dependencies.md`
**Conditional execution?** → `conditionals.md`
**Environment variables?** → `environment-variables.md`
**Artifacts?** → `artifacts.md`
**Parallel execution?** → `workflows/build-matrix.md`
**Debugging config errors?** → `defining-steps.md`, then specific step type in `step-types.md`
