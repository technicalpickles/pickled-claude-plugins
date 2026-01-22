# ci-cd-tools Plugin

CI/CD pipeline tools and integrations for debugging build failures and developing pipelines.

## Commands

### /fix-ci

Start an iterative CI fix session to systematically investigate and fix CI failures through a structured workflow. Analyzes build failures, applies fixes, verifies locally, and tracks progress until builds pass.

**Usage:**
```
/fix-ci [buildkite-url]
```

If no URL is provided, infers the build from the current branch.

## Skills

### working-with-buildkite-builds

Use when working with Buildkite CI - checking status, investigating failures, and reproducing issues locally. Provides workflows for monitoring builds, progressive failure investigation, and local reproduction strategies.

**Key capabilities:**
- Check CI status for current branch or PR
- Investigate build failures with detailed logs
- Monitor builds in real-time
- Reproduce failures locally
- Progressive disclosure pattern for efficient debugging

### developing-buildkite-pipelines

Use when creating or modifying Buildkite pipeline configurations and working with buildkite-builder DSL.

## Installation

```bash
/plugin install ci-cd-tools@technicalpickles-marketplace
```
