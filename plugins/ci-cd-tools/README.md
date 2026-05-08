# ci-cd-tools Plugin

CI/CD pipeline tools and integrations for debugging build failures.

## Skills

### fixing-ci

The iterative-fix loop. Drives verify-locally → push → check → iterate for a failing Buildkite build until it's green or you've hit the iteration cap. Investigation is delegated to `buildkite:investigating-builds`.

Activates on intent like "fix CI", "make CI green", "iterate on this build". See `skills/fixing-ci/SKILL.md` for the input contract and full loop.

## Commands

### /fix-ci

Start an iterative CI fix session. Resolves the input interactively (build URL / PR / branch / cwd), optionally creates a tracking document, then runs the `fixing-ci` skill.

**Usage:**
```
/fix-ci [buildkite-url]
```

If no URL is provided, infers from the current branch's open PR.

## Note

Buildkite skills (investigating builds, developing pipelines) live in the `buildkite` plugin. Install it for build investigation and pipeline development capabilities — `fixing-ci` depends on `buildkite:investigating-builds` for the investigation step.

## Installation

Requires the [pickled-claude-plugins marketplace](../../README.md#installation). Then:

```bash
/plugin install ci-cd-tools@pickled-claude-plugins
```
