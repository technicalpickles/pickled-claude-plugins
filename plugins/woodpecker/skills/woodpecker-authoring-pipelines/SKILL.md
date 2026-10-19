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

`woodpecker-cli exec` runs a pipeline on the local machine. It defaults the event to `manual`, which skips any step filtered to `push`, so pass `--pipeline-event push`. What it mounts and how services behave depend on the backend and the machine; see [references/runtime-facts.md](references/runtime-facts.md#local-runs-with-exec).

## Where "works locally, fails in CI" comes from

The shell, the user a step runs as, how services are named and what the checkout looks like all depend on the pipeline's backend, image and settings, so don't assume them. Add a throwaway probe step that prints `id`, `ls -l /bin/sh` and `ls -ld .git`, read its log, and fix against what it shows. Probes and the documented behavior (`failure: ignore`, skipped steps, event filters) are in [references/runtime-facts.md](references/runtime-facts.md).

## Conventions

Trigger rules, base images and file layout are choices each repo makes. Read the repo's own CLAUDE.md and copy a sibling repo's pipeline before inventing structure.
