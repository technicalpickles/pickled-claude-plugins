# Woodpecker: what's fixed and what varies

Whether a step runs as root, which shell it gets, how services are named, and what a bind mount looks like all depend on the deployment: the backend (Docker, Kubernetes, local), the step image, and the pipeline's own settings. None of that is stated here as fact. This file keeps only what comes from the CLI's own behavior or the Woodpecker docs, and gives probes for the rest.

## Find out, don't assume

When a step behaves differently than it did locally, add a throwaway step to the pipeline that prints the environment, then read its log:

```yaml
steps:
  - name: probe
    image: <the same image the failing step uses>
    commands:
      - id                      # user the step runs as
      - ls -l /bin/sh           # which shell `commands` run under
      - echo "$CI_PIPELINE_EVENT $CI_COMMIT_BRANCH"
      - ls -ld .git             # directory or file
      - getent hosts <service>  # does a service name resolve
```

Check the repo's own CLAUDE.md and sibling pipelines for conventions that already answer these.

## Documented behavior

- **`failure: ignore`** lets a step fail without failing the pipeline. A passing pipeline can still have a red step, so check step states when something seems off. Use it for advisory checks, and remove it when the check should gate merges.
- **Steps after a failure** are skipped unless they opt in with `when: status: [failure]`. The first failure is the usual cause.
- **Event filters** (`when: event:`) are a per-repo choice. With a push-only filter, pull requests still get a forge status because the status attaches to the commit.
- **The linter** may recommend a `when:` block with an `event` filter. Run `woodpecker-cli lint` to see what the installed version says.

## Local runs with `exec`

From `woodpecker-cli exec --help` (confirmed on 3.18.1):

- `--pipeline-event` sets `CI_PIPELINE_EVENT` and **defaults to `manual`**. A pipeline whose steps filter on `event: push` skips every step unless you pass `--pipeline-event push`.
- `--backend-engine` picks the backend (default: auto-detect). `--local` runs from the local directory, `--repo-path` points at the repository, and `--commit-branch` sets `CI_COMMIT_BRANCH` (default `main`).

```bash
woodpecker-cli exec --local --repo-path "$CLONE" --backend-engine docker \
  --pipeline-event push --commit-branch "$BRANCH" --commit-sha "$SHA" \
  "$CLONE/.woodpecker.yml"
```

What a local run mounts and whether services start depend on the backend and the machine. If a step that works on the server fails under `exec`, run the probe step both ways and compare. One thing to rule out for steps that call git: in a linked git worktree `.git` is a file, not a directory, so point `--repo-path` at a regular clone if that matters.
