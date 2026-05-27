# Common GHA failure patterns

A field guide to recognizing what kind of failure you're looking at, so you don't spend an hour on a transient flake or rerun a real bug ten times.

## Matrix jobs

When a workflow uses `strategy.matrix`, each leg is a separate job named like `test (3.11, ubuntu-latest)`. Two failure modes look the same on the surface:

**Root failure.** One specific leg has the bug — say, a test that only fails on Python 3.10. With `fail-fast: true` (the default), the first leg to fail cancels the rest, which then show up as `failure` too even though they never finished.

To find the root: sort failed jobs by `startedAt` and take the earliest one with `conclusion: failure` (not `cancelled`). The snapshot's failed-step output for that job is where the actual bug is.

**Genuine multi-leg failure.** Every leg failed independently with `fail-fast: false`. Each leg's log is its own story. The snapshot will show all of them; treat each as a separate investigation.

`jq` to find the earliest failure:

```bash
gh run view <id> --json jobs \
  | jq '[.jobs[] | select(.conclusion=="failure")] | sort_by(.startedAt) | .[0]'
```

## `needs:` cascade

A job with `conclusion: skipped` because an upstream `needs:` job failed is **not the bug**. The snapshot marks these as `⊘ <name> (skipped, dependency failed)`. Always trace upstream — find the job that has `conclusion: failure` and no failed dependency.

If multiple jobs have `needs:` chains, sketch the graph mentally before pointing at any one of them. The bug is at the root of the failure tree.

## Reusable workflows

When the workflow uses `uses: org/repo/.github/workflows/x.yml@ref`, the parent run shows a step like "Calling workflow x.yml" that's marked failed. The actual error log lives in the **called workflow's own run**, not the parent.

From the parent run, follow the called-workflow URL (visible in `gh run view <parent-id> --json jobs | jq '.jobs[].url'` or in the GHA UI). Re-run `gha-snapshot` on the called workflow's run.

This is a common source of "the snapshot says it failed but I can't see why" confusion. The output you want is one level deeper.

## OIDC / permissions errors

Symptom in logs:

```
Error: Resource not accessible by integration
Error: Could not create OIDC token (HTTP 403)
```

This is almost always a missing or insufficient `permissions:` block in the workflow. Common minimum permissions:

```yaml
permissions:
  contents: read           # checkout
  id-token: write          # OIDC (e.g., aws-actions/configure-aws-credentials)
  pull-requests: write     # commenting on PRs
  issues: write            # creating/closing issues
  packages: write          # pushing container images
```

Do NOT rerun — the permissions need a code change.

## Secret-related failures

Two distinct cases:

**Redacted secrets in logs.** Lines containing `***` are GHA's secret masking — secrets you referenced via `${{ secrets.FOO }}` are replaced before the log is written. This is good; it means masking is working. The bug is rarely in the redaction itself.

**Missing secrets.** Symptom is usually an empty string in a place that should have a value, leading to downstream errors like `401 Unauthorized` or `Cannot read property 'X' of undefined`. Check whether the secret is defined at the right scope (repo / environment / org) and whether the job has `environment:` set if the secret is environment-scoped.

`::add-mask::` annotations in logs are GHA's tool for masking values that aren't from `secrets.*`. If you see them, someone is dynamically masking — usually fine.

## Transient infrastructure flakes

Reasonable candidates for `gh run rerun --failed`:

- **Docker Hub rate limits.** `toomanyrequests: You have reached your pull rate limit` or `429 Too Many Requests` when pulling base images. Often resolved by waiting or by authenticating with `docker/login-action`.
- **Registry timeouts.** `npm ERR! network timeout`, `Failed to fetch ... 503`, `Could not resolve host` for `pypi.org` / `registry.npmjs.org` / `crates.io`. Usually transient.
- **Runner provisioning.** `Worker initialization timeout`, `Error response from daemon: ...`, `Failed to download action`. The runner host had a bad start; rerun on a fresh runner usually works.
- **GitHub-side issues.** Cross-check https://www.githubstatus.com — if Actions is degraded, rerun after the incident is resolved.

If unsure whether the failure is transient, prefer to investigate first. Repeated reruns on a real bug just waste minutes.

## Cancelled vs failed

A run cancelled because a newer commit was pushed to the same branch shows up as `conclusion: cancelled` (not `failure`). This is **not a bug** — the workflow uses `concurrency.cancel-in-progress: true` and behaved correctly. Don't investigate cancelled runs as if they were failures.

Tell the difference:

```bash
gh run view <id> --json conclusion
# "cancelled" → concurrency cancellation (usually); fine
# "failure"   → real failure; investigate
```

## Action version drift

When an action's API changes between major versions, you'll see:

```
Error: Input required and not supplied: <name>
Error: Unknown argument '<flag>'
Warning: This action is deprecated, please use ...
```

Don't guess at the right input from training data. Check the action's releases:

```bash
gh release list --repo actions/<name>
gh release view <tag> --repo actions/<name>
```

If the workflow pins `@v3` but `v4` deprecated an input, the fix is either bumping the major or restoring the old input depending on what the workflow needs.

## Workflow files not running at all

Symptoms: a PR didn't trigger CI, or `gh workflow run` says "could not find workflow".

Likely causes (no rerun will fix any of these):

- Workflow file is malformed YAML. `gh workflow view <name>` will show a syntax error, or `gh api repos/{owner}/{repo}/actions/workflows` will omit it.
- `on:` triggers don't match the event. A workflow with `on: push` won't run for `pull_request`.
- Path filters (`paths:`, `paths-ignore:`) excluded the changed files.
- The workflow is disabled. `gh workflow list` shows status; `gh workflow enable <name>` re-enables.
- Fork PRs: by default, secrets and some triggers don't run for first-time contributors. Settings → Actions → General has the policy.
