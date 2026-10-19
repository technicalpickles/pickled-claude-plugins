# Woodpecker runtime facts

These come from one setup: Woodpecker 3.19.0 with the Docker backend and Debian-based step images. Each item names what it depends on. Treat them as strong defaults, not guarantees: when a fact decides what you write, check it on the user's setup first (the check is given where one is cheap). "Observed" means a real pipeline hit it. "Upstream" means it comes from the documentation or the CLI's own behavior and wasn't hit here.

## Shell

- **Observed, depends on the step image:** `commands` ran under `sh`, which is dash on Debian-based images. `[[ ... ]]`, `source`, arrays and `${var,,}` failed with syntax errors. Check with `ls -l /bin/sh` in the image (Alpine's is busybox ash, which also lacks most bashisms). Use POSIX `[ ... ]` and `.`, or run `bash -c '...'` in an image that has bash.

## Users and permissions

- **Observed, depends on the image and `user:` settings:** cloned files were owned by root and steps ran as root. A test that makes a file unreadable and expects an error read it anyway. Check with `id` in a step. If the image or step sets a non-root user, this doesn't apply. Tests that need a non-root user have to switch to one in a step, and write only to directories that user owns (such as `/tmp`).

## Services

- **Observed, Docker backend:** a service declared under `services:` was reachable at its service name as a hostname, and `localhost` pointed at the step's own container. Other backends (Kubernetes, local) may wire services differently; check the docs for the backend in use. A database service may need a wait loop before the first connection.

## Failure handling

- **Upstream, also seen:** `failure: ignore` lets a step fail without failing the pipeline. A passing pipeline can still have a red step, so check step states when something seems off. Use it for advisory checks, and remove it when the check should gate merges.
- **Observed:** when a step fails, later steps showed as `skipped`. The first failure is the cause. **Upstream:** steps that opt in with `when: status: [failure]` still run after a failure.

## Triggers

- **Observed, CLI 3.19.0:** the linter recommends a `when:` block with an `event` filter on each step or on the workflow. Run `woodpecker-cli lint` to see what the installed version says.
- **Upstream:** with a push-only filter, pull requests still get a forge status because the status attaches to the commit. Event filters are a per-repo choice.

## Local runs

- **Observed, Docker on OrbStack, macOS:** `woodpecker-cli exec` runs a full pipeline locally, services included (a Postgres `services:` entry worked).
- **Observed, and confirmed in `exec --help` (3.18.1):** pass `--pipeline-event push` (or whatever event the `when:` blocks name). `exec` defaults the event to `manual`, so a pipeline filtered to `push` skips every step.
- **Observed once; the cause (a `.git` file pointing outside the mount) should apply to any Docker bind mount, but wasn't tried elsewhere:** run it against a real clone, not a linked git worktree. A worktree's `.git` is a file pointing outside the mounted directory, which breaks steps that call `git rev-parse --git-dir`. Cloning HEAD into a temp dir (`git clone --local`) and passing `--repo-path` works, but uncommitted changes aren't tested.
- **Upstream:** `--backend-engine` picks Docker or the local backend; `--local` runs from the local directory; `--commit-branch` sets `CI_COMMIT_BRANCH` (default `main`).

Example:

```bash
woodpecker-cli exec --local --repo-path "$CLONE" --backend-engine docker \
  --pipeline-event push --commit-branch "$BRANCH" --commit-sha "$SHA" \
  "$CLONE/.woodpecker.yml"
```
