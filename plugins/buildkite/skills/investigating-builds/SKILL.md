---
name: investigating-builds
description: Use when the user is working with an existing Buildkite CI run and wants to understand, diagnose, or act on it. Strong signals: a buildkite.com URL, the word "buildkite", the `bk` CLI, the `bktide` tool, or a reference to a specific pipeline, build, or job. Covers intents like: "why did this build fail", "what's flaking", "summarize pass/fail rates across recent builds", "pull logs for this job", "figure out the exact command CI ran so I can reproduce it locally" (often via docker-compose), "why didn't my downstream build trigger", and debugging `bk`/`bktide` behavior itself (auth failures, query errors, sandbox issues). Do NOT use for authoring pipeline YAML or adding pipeline steps (that's `buildkite:developing-pipelines`). Do NOT use for meta-work on the Claude buildkite plugin itself (editing SKILL.md, reviewing pickled-claude-plugins PRs, adding reference docs under the plugin's directory). Do NOT use for GitHub Actions, PR review, app code changes, git merge conflicts, or local `bk` config (`~/.bk/config.yml`) that don't involve investigating an actual build. This skill reads and investigates CI runs that already exist.
---

# Working with Buildkite Builds

Check status, investigate failures, and reproduce them locally for Buildkite builds that already exist.

## Tools, in order

**Always use Buildkite-native tools. Don't fall back to `gh pr view`/`gh pr checks` or the GitHub API**: GitHub shows only a summary and loses annotations, logs, and the broken-vs-failed distinction. If one Buildkite tool fails, move to the next tier below rather than abandoning Buildkite.

1. **`npx bktide@latest snapshot <buildkite-url>`** (use this first). Parses any build or step URL, downloads build metadata, annotations, and logs for failed steps into files you can grep and re-read without more API calls. `bktide snapshot --help` for options, `bktide prime` for LLM-oriented usage.

   ```
   ./tmp/bktide/snapshots/<org>/<pipeline>/<build>/
   ├── manifest.json      # Step index with states and exit codes
   ├── build.json         # Full build metadata
   ├── annotations.json   # Build annotations
   └── steps/<NN-step-name>/{log.txt,step.json}
   ```

2. **Other bktide commands** for quick queries: `pipelines <org>`, `builds <org>/<pipeline>`, `build <org>/<pipeline>#<build>`, `annotations <org>/<pipeline>#<build>`, and the one write capability, `build create` / `build rebuild` (see below).

3. **MCP tools** (fallback, and the only way to wait on or unblock a build): `buildkite:get_build`, `list_builds`, `list_annotations`, `get_pipeline`, `list_pipelines`, `wait_for_build`, `get_logs`, `get_logs_info`, `list_artifacts`, `unblock_job`. Start with `detail_level: "summary"` and filter with `job_state: "failed"`.

Full capability matrix: [references/tool-capabilities.md](references/tool-capabilities.md). The tool preference order can be overridden in `~/.config/pickled-claude-plugins/buildkite.yml`; a PreToolUse hook enforces it by intercepting `bk` CLI commands that overlap with bktide.

## Investigating a failed build

Snapshot the URL, then:

**Filter to root failures.** Most builds have 1-3 root failures and dozens-to-hundreds of dependent BROKEN steps. Counting BROKEN/RUNNING steps as failures sends you down rabbit holes investigating noise.

First, see the state distribution:

```bash
jq -r '.steps[].state' ./tmp/bktide/snapshots/<org>/<pipeline>/<build>/manifest.json | sort | uniq -c | sort -rn
```

**Only these are real failures:**
- Steps with state `FINISHED` (or `FAILED`) AND non-zero `exit_status`

**These are NOT failures — do not count or investigate them:**
- **BROKEN** — Downstream dependencies that never ran. Auto-resolve when the root failure is fixed.
- **RUNNING** — Still in progress.
- **WAITING** / **SCHEDULED** — Haven't started yet.
- **CANCELED** — Manually or automatically canceled.

Find actual root failures:

```bash
jq -r '.steps[] | select((.state == "FINISHED" or .state == "FAILED") and .exit_status != null and .exit_status != 0) | "\(.id): \(.label) (exit \(.exit_status))"' ./tmp/bktide/snapshots/<org>/<pipeline>/<build>/manifest.json
```

**Example:** A summary reads "466 steps: 43 passed, 397 failed, 361 running" — filtering reveals 1 actual failure (e.g. codeownership validation) and 396 BROKEN dependents. Fix the root and everything else passes.

Then read the failing step's `steps/<step-id>/log.txt` (or `grep -r "Error\|Failed\|Exception"` across `steps/`), and check `annotations.json`: large projects summarize test failures there, small ones usually have none. See [references/buildkite-states.md](references/buildkite-states.md) and [references/annotation-patterns.md](references/annotation-patterns.md).

### Logs via MCP (when snapshot isn't an option)

```javascript
mcp__MCPProxy__call_tool('buildkite:get_build', {
  org_slug: '<org>',
  pipeline_slug: '<pipeline>',
  build_number: '<build-number>',
  detail_level: 'detailed',
  job_state: 'failed',
});
```

Match the job by `label` and take its `uuid`, then:

```javascript
mcp__MCPProxy__call_tool('buildkite:get_logs', {
  org_slug: '<org>',
  pipeline_slug: '<pipeline>',
  build_number: '<build-number>',
  job_id: '<job-uuid>',
});
```

**Common Issues:**

- **"job not found" error**: You likely provided a step ID instead of a job UUID. Step IDs come from URLs (`sid=019a5f...`). Job UUIDs come from `get_build` API responses.
- **Empty logs**: The job may not have started yet. Check the job's `state` field first.

## After a push

Find the build with [scripts/find-commit-builds.js](scripts/find-commit-builds.js) `<org> <commit-sha>`, then wait with MCP `buildkite:wait_for_build` (`timeout: 1800, poll_interval: 30`), or in the background with [scripts/wait-for-build.js](scripts/wait-for-build.js) `<org> <pipeline> <build> --timeout 1800 --interval 30` (exit 0 passed, 1 failed, 2 canceled, 3 timeout). Don't poll in the foreground.

## Blocked builds

A `blocked` build waits on a manual step. Find the job with `state: "blocked"` in `get_build` (`detail_level: "detailed"`), check its label for what approval it needs, and unblock only if appropriate:

```javascript
mcp__MCPProxy__call_tool('buildkite:unblock_job', {
  org_slug: '<org>',
  pipeline_slug: '<pipeline>',
  build_number: '<build-number>',
  job_id: '<job-id>',
  fields: {}, // Optional form fields if the block step has inputs
});
```

## Reproducing a failure locally

1. **Extract the command from the log.** Docker-compose steps log it as `:docker: Running /bin/sh -e -c '<command>' in service <service>`; with shell trace on, look for `+ ` lines.
2. **Find the environment:** vars printed in the log, `env:` blocks in `.buildkite/pipeline.yml` (or the buildkite-builder DSL), and Buildkite defaults like `CI=true` ([references/buildkite-environment-variables.md](references/buildkite-environment-variables.md)).
3. **Translate:** run the command directly first; if it ran in Docker, `docker-compose run [-e CI=true ...] <service> <command>`. Drop CI-only flags (`--parallel 4` to 1, `--format buildkite` to progress) and skip `buildkite-agent artifact download`.
4. **If it can't run locally** (internal infrastructure, secrets, cross-agent parallelism, artifacts from earlier steps): push a debug branch with verbose flags or `env | sort`, inspect artifacts (`buildkite:list_artifacts`, JUnit XML, coverage), or fix from logs and artifacts alone. Plugins for artifacts, notifications, or caching don't block local reproduction.

## Triggering or rebuilding a build

Some events that feel like they should start a new build don't. GitHub's "ready for review" event, for example, does not trigger a new Buildkite build — only pushes do. If you need a build for the current state without a new commit, don't push an empty commit as a workaround; trigger one directly:

```bash
# Start a new build (auto-detects org/pipeline/commit/branch from the current git checkout)
npx bktide@latest build create

# Watch it through to completion
npx bktide@latest build create --watch

# Re-run an existing build with its original commit/branch/message
npx bktide@latest build rebuild <org>/<pipeline>/<build-number>
npx bktide@latest build rebuild <buildkite-build-url>
```

Flags (`--commit`, `--branch`, `--message`, `--env`) override git auto-detection; run `bktide build create --help` for the full list. This is the one write operation bktide supports — it's the direct replacement for `bk build create`/`bk build retry`, which the buildkite tool-preference hook blocks in favor of this command.

## References

- [references/troubleshooting.md](references/troubleshooting.md): common errors and a decision tree for when stuck
- [references/url-parsing.md](references/url-parsing.md): Buildkite URLs, step IDs vs job UUIDs
- [scripts/parse-buildkite-url.js](scripts/parse-buildkite-url.js), [scripts/get-build-logs.js](scripts/get-build-logs.js): URL parsing and label-to-UUID log retrieval; run with `--help`
