# ci-cd-tools Plugin

CI/CD pipeline tools and integrations for debugging build failures.

## Commands

### /fix-ci

Start an iterative CI fix session to systematically investigate and fix CI failures through a structured workflow. Analyzes build failures, applies fixes, verifies locally, and tracks progress until builds pass. Uses the `buildkite:investigating-builds` skill for build investigation.

**Usage:**
```
/fix-ci [buildkite-url]
```

If no URL is provided, infers the build from the current branch.

## Note

Buildkite skills have moved to the `buildkite` plugin. Install it for build investigation and pipeline development capabilities.

## Installation

Requires the [pickled-claude-plugins marketplace](../../README.md#installation). Then:

```bash
/plugin install ci-cd-tools@pickled-claude-plugins
```
