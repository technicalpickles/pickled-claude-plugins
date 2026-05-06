---
name: fixing-ci
description: Use when CI is failing on a branch, PR, or specific Buildkite build and the user wants to iteratively fix it through verify-locally → push → check → iterate. Strong signals: "fix CI", "make CI green", "CI is failing", "tests are failing in Buildkite", "iterate on this build", a Buildkite build URL paired with intent to push fixes, a PR with a red check the user wants to make green, or repeat-push debugging. Covers verify-fix-locally workflows (rspec, jest, lint, type checking before pushing), iteration tracking across multiple builds, and knowing when to step back after N failed attempts. Do NOT use for first-time investigation of a build (use `buildkite:investigating-builds` for "why did this fail" without a fix-and-push intent). Do NOT use for authoring pipeline YAML or adding pipeline steps (use `buildkite:developing-pipelines`). Do NOT use for GitHub Actions debugging or non-Buildkite CI. This skill drives the fix loop; investigation is delegated to `buildkite:investigating-builds`.
---

# Fixing CI

## Overview

This skill drives an iterative CI fix session: investigate the failure (via the Buildkite investigation skill), apply a fix, verify it locally, push, watch the new build, and iterate until green or until you've hit the iteration cap and need to step back.

The scope is the **fix loop only** — investigation is delegated to `buildkite:investigating-builds`, which already covers `bktide snapshot`, log reading, and failure-pattern recognition.

## When to Use

- You have a failing CI build and want to push fixes until it goes green
- You want to verify changes locally before each push (saves CI cycles)
- You're iterating on fixes across multiple builds and need to know when to step back

## When NOT to Use

- First-time "why did this fail" investigation with no fix-and-push intent → use `buildkite:investigating-builds` directly
- Authoring or modifying pipeline YAML → use `buildkite:developing-pipelines`
- GitHub Actions, CircleCI, or non-Buildkite CI

## Input Contract

The skill needs to know what to fix. Any one of these inputs is sufficient:

- **`build_url`** — A Buildkite build URL (e.g. `https://buildkite.com/org/pipeline/builds/123`)
- **`pr`** — A GitHub PR number (resolves to its latest failing build for that branch)
- **`branch`** — A git branch name (resolves to its open PR's latest failing build)

### Resolving inputs

If the caller provides one of the above, use it directly. Otherwise:

1. **From cwd**: read the current git branch (`git branch --show-current`), look for an open PR (`gh pr view --json number,headRefName`), find its latest failing build via the `buildkite:investigating-builds` skill's "Checking Current Branch/PR Status" workflow.
2. **If cwd doesn't resolve cleanly** (no branch, no open PR, no failing build): the caller (slash-command wrapper or workflow agent) is responsible for either asking the user or failing with a clear message. This skill assumes resolution is done before its loop starts.
