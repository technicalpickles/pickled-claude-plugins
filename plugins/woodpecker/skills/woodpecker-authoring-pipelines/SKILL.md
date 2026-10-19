---
name: woodpecker-authoring-pipelines
description: Use when writing or editing `.woodpecker.yml` or `.woodpecker/*.yaml`, porting a GitHub Actions or other CI config to Woodpecker, checking whether a Woodpecker config is valid, or when a Woodpecker step behaves differently than it does locally (shell syntax, file permissions, a service on localhost).
---

# Authoring Woodpecker pipelines

## Validate before pushing

```bash
woodpecker-cli lint .woodpecker.yml    # a file, or a .woodpecker/ directory
```

Exit 0 prints `Config is valid`. Errors print one line each and exit 1. It needs no server and no login, so it works on any machine with the CLI. A warning like "consider adding a `when` block with an `event` filter" is advice, not an error: without one, a step runs on every event.

`woodpecker-cli exec` runs a pipeline locally in Docker, services included. Pass `--pipeline-event push` (the default is `manual`, which skips steps filtered to `push`) and run it from a real clone, not a linked git worktree. See [references/runtime-facts.md](references/runtime-facts.md#local-runs) for a full invocation.

## Where "works locally, fails in CI" comes from

These were seen on a Docker-backend setup with Debian-based images. Each depends on the image, user or backend, so confirm before relying on one. Details and the checks are in [references/runtime-facts.md](references/runtime-facts.md).

- Step `commands` run under `sh` (dash on Debian images; check the image), not bash. Bashisms such as `[[ ]]` and `source` fail.
- With default settings the clone is owned by root and steps run as root (a `user:` setting or non-root image changes that). Tests that check file permissions or refuse to run as root behave differently.
- On the Docker backend, services are reached by their service name (`postgres:5432`), not `localhost`.
- A step with `failure: ignore` can fail while the pipeline shows green.

## Conventions

Trigger rules, base images and file layout are choices each repo makes. Read the repo's own CLAUDE.md and copy a sibling repo's pipeline before inventing structure.
