# `gh` CLI cheatsheet for GHA investigation

Quick reference for the `gh` subcommands you'll reach for when `gha-snapshot` doesn't expose what you need. All commands assume `gh auth login` is already done.

## `gh run list`

List runs with filters.

```bash
gh run list --branch main --status failure --limit 5
gh run list --workflow ci.yml --limit 10
gh run list --user octocat --event push
gh run list --created '>2026-05-01'
```

Useful flags:

| Flag | Effect |
|------|--------|
| `--branch <name>` | Filter to one branch |
| `--workflow <file-or-name>` | Filter to one workflow |
| `--status <state>` | `queued`, `in_progress`, `completed`, `success`, `failure`, `cancelled`, `skipped` |
| `--event <event>` | `push`, `pull_request`, `workflow_dispatch`, etc. |
| `--user <login>` | Triggered by a specific user |
| `--created <expr>` | Date filter (`>2026-05-01`, `2026-05-01..2026-05-15`) |
| `--limit N` | Max rows |
| `--json <fields>` | Switch to JSON output for scripting |

JSON fields for `--json`:

```
attempt, conclusion, createdAt, databaseId, displayTitle, event, headBranch,
headSha, name, number, startedAt, status, updatedAt, url, workflowDatabaseId,
workflowName
```

## `gh run view`

Inspect a single run.

```bash
gh run view <run-id>                     # human summary
gh run view <run-id> --json jobs         # all jobs
gh run view <run-id> --log               # full log (huge — use sparingly)
gh run view <run-id> --log-failed        # failed-step logs only
gh run view <run-id> --web               # open in browser
gh run view <run-id> --job <job-id>      # one job's log only
```

JSON fields for `--json` (run-level):

```
artifacts, conclusion, createdAt, databaseId, displayTitle, event, headBranch,
headSha, jobs, name, number, startedAt, status, updatedAt, url, workflowDatabaseId,
workflowName
```

Inside `jobs`, each job has: `conclusion, completedAt, databaseId, name, startedAt, status, steps, url`. Each step has: `conclusion, name, number, status`.

## `gh run rerun`

```bash
gh run rerun <run-id>              # rerun all jobs
gh run rerun <run-id> --failed     # rerun only failed jobs
gh run rerun <run-id> --job <id>   # rerun one job
```

See SKILL.md's "When to rerun vs. fix" — don't rerun assertion failures or compile errors.

## `gh run watch`

Block until a run finishes.

```bash
gh run watch <run-id>
gh run watch <run-id> --exit-status     # exits non-zero if the run failed
gh run watch                            # picks the most recent run on the branch
```

Avoid in interactive Claude sessions — blocks the terminal. Prefer polling with `gh run view --json status,conclusion` if you need to know when a run finishes.

## `gh pr checks`

Show checks for a PR (combines GHA + other status providers).

```bash
gh pr checks <pr-number>
gh pr checks <pr-number> --watch
gh pr checks <pr-number> --json name,state,link,workflow,bucket
```

`state` values: `SUCCESS`, `FAILURE`, `PENDING`, `SKIPPED`, `CANCELLED`. `link` points at the specific run + job. `bucket` is a rolled-up category (`pass`, `fail`, `pending`, `skipping`).

## `gh workflow`

```bash
gh workflow list                          # all workflows in the repo
gh workflow view <name-or-id>             # YAML + recent runs
gh workflow run <name>                    # manually trigger a workflow_dispatch
gh workflow enable <name>
gh workflow disable <name>
```

## `gh api` — raw access

For things the wrappers don't cover.

```bash
gh api repos/{owner}/{repo}/actions/runs/{run_id}
gh api repos/{owner}/{repo}/actions/runs/{run_id}/jobs
gh api repos/{owner}/{repo}/actions/runs/{run_id}/attempts/{attempt_number}
gh api repos/{owner}/{repo}/check-runs/{check_run_id}/annotations
gh api repos/{owner}/{repo}/actions/runs/{run_id}/logs > logs.zip   # signed redirect to log archive
```

GraphQL examples:

```bash
gh api graphql -f query='
  query($owner:String!, $repo:String!, $run:Int!) {
    repository(owner:$owner, name:$repo) {
      object(expression:"HEAD") { ... on Commit { oid } }
    }
  }' -F owner=octocat -F repo=Hello-World -F run=123
```

## `jq` patterns

Most-failed workflow names over the last 50 runs:

```bash
gh run list --limit 50 --status failure --json workflowName \
  | jq -r 'group_by(.workflowName) | map({k:.[0].workflowName, n:length}) | sort_by(-.n) | .[] | "\(.n)\t\(.k)"'
```

All failed step names in a run:

```bash
gh run view <id> --json jobs \
  | jq -r '.jobs[] | select(.conclusion=="failure") | .name as $j | .steps[] | select(.conclusion=="failure") | "\($j) → \(.name)"'
```

Was this run a re-run?

```bash
gh run view <id> --json status,conclusion,attempt | jq '.attempt'
```

Earliest-failing matrix leg (for cascade triage):

```bash
gh run view <id> --json jobs \
  | jq '[.jobs[] | select(.conclusion=="failure")] | sort_by(.startedAt) | .[0].name'
```
