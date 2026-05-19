---
name: investigating-runs
description: Use when the user is working with an existing GitHub Actions run and wants to understand, diagnose, or act on it. Strong signals: a `github.com/.../actions/runs/...` URL, the phrase "GitHub Actions" or "GHA", the `gh run` CLI, a reference to a failing workflow / job / check, a PR with red GHA checks. Covers intents like "why did this run fail", "what step broke", "pull logs for the failing job", "find the root failure in this matrix run", "is this CI flake or a real bug". Do NOT use for authoring `.github/workflows/*.yml` (not in scope this plugin). Do NOT use for Buildkite (use the `buildkite` plugin). Do NOT use for local-only CI debugging where no remote run exists yet, merge conflicts, or meta-work on this plugin itself.
---

# Investigating GitHub Actions Runs

## Overview

This skill helps you investigate failing GitHub Actions runs. It covers **checking status, finding the root failure, and reading log output efficiently** — not authoring workflow YAML, not driving a fix-then-rerun loop. Load it when working with an existing run (failed CI, red PR check, "why is this broken").

## Why `gha-snapshot`?

One command, one ref, gets you everything: run metadata, per-job status, the failed step's log tail, and annotations — in a single readable block. `gh run view --log-failed` is a firehose; `gha-snapshot` distills it.

## Tool hierarchy

Use in this order. Don't skip ahead unless the current tier can't answer the question.

### 1. `gha-snapshot` (primary)

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/gha-snapshot <ref>
```

Accepts any of:

| Input | Example |
|-------|---------|
| Full URL | `gha-snapshot https://github.com/octocat/Hello-World/actions/runs/123` |
| Run ID (uses cwd's repo) | `gha-snapshot 123` |
| PR number | `gha-snapshot --pr 42` |
| Default (latest failed run on current branch) | `gha-snapshot` |

Flags: `--tail N` controls how many lines of failed-step log to include per failed job (default 50).

Exit 0 = snapshot rendered (even if the run failed). Exit 1 = couldn't resolve a run.

### 2. Raw `gh` CLI (secondary)

When the snapshot doesn't expose what you need:

```bash
gh run list --branch <branch> --status failure --limit 5
gh run view <run-id> --json jobs,conclusion,headSha,event
gh run view <run-id> --log         # full log (huge)
gh run view <run-id> --log-failed  # failed steps only
gh run rerun <run-id> --failed     # transient infra only — see below
gh pr checks <pr-num>
gh workflow view <workflow>
```

See [references/gh-cheatsheet.md](references/gh-cheatsheet.md) for `--json` field names and `jq` patterns.

### 3. `gh api` (fallback)

For things the wrappers don't cover: GraphQL queries, raw check-run annotations, paged listings.

```bash
gh api repos/{owner}/{repo}/actions/runs/{run_id}/jobs
gh api repos/{owner}/{repo}/check-runs/{check_id}/annotations
```

## Reading the snapshot output

A `gha-snapshot` block has five sections in fixed order:

```
Run: <workflow> #<num>         ← header: name, conclusion, duration, trigger, sha, URL
Status: <conclusion> (<dur>)
Trigger: <event> on <branch> @ <sha>
URL: <run-url>

Jobs:                          ← per-job status with icon (✓ success, ✗ failure, ⊘ skipped)
  ✓ build (2m 14s)             ← passed jobs noted but not detailed
  ✗ test (1m 03s) — failed at step "..."
  ⊘ deploy (skipped, dependency failed)

Failed step output (...)       ← log tail for each failed step's named step
  ...
  FAIL ...

Annotations:                   ← grouped by job, `::error::` / `::warning::` / `::notice::`
  test: ::error file=...,line=...::message

Links:                         ← run URL + per-failed-job URLs
  Run:  ...
  test: .../job/<id>
```

The most valuable section is usually **Failed step output**. It's the part `gh run view --log-failed` would have buried under hundreds of unrelated lines.

## Distinguishing root failures from cascades

A common mistake: pointing at the wrong job as "the bug."

- **Matrix jobs:** When `fail-fast: true`, one matrix leg's failure cancels the rest. The cancelled legs are marked `failure` but aren't the bug. Find the leg with the earliest failure timestamp.
- **`needs:` cascade:** A job with conclusion `skipped` because its dependency failed is not the bug. Trace upstream to the failed dependency.
- **Reusable workflows:** A failure inside `uses: org/repo/.github/workflows/x.yml@ref` shows in the parent run, but the real log is in the called workflow's own run. The snapshot's link section will point at the parent; click through to the called workflow.

See [references/failure-patterns.md](references/failure-patterns.md) for more cases.

## Annotations

GitHub Actions emits workflow commands in logs that surface as annotations:

- `::error file=path,line=N::message` — error tied to a file
- `::warning::message` — non-fatal
- `::notice::message` — informational
- `::group::title` / `::endgroup::` — bracket log sections

The snapshot's **Annotations** section extracts these from `gh run view --log-failed`. Annotations with `file=` and `line=` are usually the strongest signal for "where the bug is."

See [references/annotation-format.md](references/annotation-format.md) for the full directive reference.

## When to rerun vs. fix

Don't reflexively `gh run rerun --failed`. Rerun only when the failure is clearly **transient infrastructure**:

- Docker Hub rate limits (`429 Too Many Requests` pulling base images)
- npm / pip / cargo registry timeouts
- Runner provisioning errors (`Worker initialization timeout`, host setup failures)
- GitHub-side outages (cross-check https://www.githubstatus.com)

Never rerun for:
- Test failures, compile errors, lint errors
- Permission errors (`Resource not accessible by integration` — needs a real `permissions:` fix)
- Missing files, missing env vars

If you can't tell whether it's transient, say so to the user and ask.

## Don't speculate on action versions

When a step references `actions/<name>@v...` and the snapshot's error looks like it might be related to the action's behavior (`Error: Input ... not found`, `Unknown argument`), don't guess from training data. Check the action's releases page:

```bash
gh release list --repo actions/<name>
gh release view <tag> --repo actions/<name>
```

Action APIs change between major versions. The current state of `actions/checkout@v4` is not what was current at any given training cutoff.

## Reference docs

- [references/gh-cheatsheet.md](references/gh-cheatsheet.md) — `gh` subcommands, common flags, `--json` field names, `jq` patterns
- [references/failure-patterns.md](references/failure-patterns.md) — matrix root-vs-cascade, reusable workflow propagation, OIDC, secret leaks, transient flakes
- [references/annotation-format.md](references/annotation-format.md) — workflow command syntax and where annotations surface
