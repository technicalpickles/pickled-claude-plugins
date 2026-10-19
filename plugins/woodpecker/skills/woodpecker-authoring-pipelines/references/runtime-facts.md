# Woodpecker runtime facts

Each item says where it was seen. "Observed" means a real pipeline hit it. "Upstream" means it comes from the documentation or the CLI's own behavior and wasn't hit here.

## Shell

- **Observed:** step `commands` run under `sh`, which is dash on Debian-based images. `[[ ... ]]`, `source`, arrays and `${var,,}` fail with syntax errors. Use POSIX `[ ... ]` and `.`, or run `bash -c '...'` in an image that has bash.

## Users and permissions

- **Observed:** cloned files are owned by root and steps run as root. A test that makes a file unreadable and expects an error will read it anyway. Tests that need a non-root user have to switch to one in a step, and write only to directories that user owns (such as `/tmp`).

## Services

- **Observed:** a service declared under `services:` is reachable at its service name as a hostname. `localhost` points at the step's own container. A database service may need a wait loop before the first connection.

## Failure handling

- **Observed:** `failure: ignore` lets a step fail without failing the pipeline. A passing pipeline can still have a red step, so check step states when something seems off. Use it for advisory checks, and remove it when the check should gate merges.
- **Observed:** when a step fails, later steps show as `skipped`. The first failure is the cause.

## Triggers

- **Observed:** the CLI's linter recommends a `when:` block with an `event` filter on each step or on the workflow.
- **Upstream:** with a push-only filter, pull requests still get a forge status because the status attaches to the commit. Event filters are a per-repo choice.

## Local runs

- **Observed (Docker on OrbStack):** `woodpecker-cli exec` runs a full pipeline locally, services included (a Postgres `services:` entry worked).
- **Observed:** pass `--pipeline-event push` (or whatever event the `when:` blocks name). `exec` defaults the event to `manual`, so a pipeline filtered to `push` skips every step.
- **Observed:** run it against a real clone, not a linked git worktree. A worktree's `.git` is a file pointing outside the mounted directory, which breaks steps that call `git rev-parse --git-dir`. Cloning HEAD into a temp dir (`git clone --local`) and passing `--repo-path` works, but uncommitted changes aren't tested.
- **Upstream:** `--backend-engine` picks Docker or the local backend; `--local` runs from the local directory; `--commit-branch` sets `CI_COMMIT_BRANCH` (default `main`).

Example:

```bash
woodpecker-cli exec --local --repo-path "$CLONE" --backend-engine docker \
  --pipeline-event push --commit-branch "$BRANCH" --commit-sha "$SHA" \
  "$CLONE/.woodpecker.yml"
```
