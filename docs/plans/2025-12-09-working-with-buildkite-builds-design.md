# Working with Buildkite Builds - Design

## Overview

Rename and extend the `monitoring-buildkite-builds` skill to `working-with-buildkite-builds`, adding a comprehensive workflow for reproducing build failures locally.

## Change Summary

**Rename:** `monitoring-buildkite-builds` → `working-with-buildkite-builds`

**Updated description:**
> Use when working with Buildkite CI - checking status, investigating failures, and reproducing issues locally. Provides workflows for monitoring builds, progressive failure investigation, and local reproduction strategies.

**New workflow:** "Reproducing Build Failures Locally"

**New reference:** `references/buildkite-environment-variables.md`

## New Workflow: Reproducing Build Failures Locally

This workflow follows three phases after investigating a failed build:

### Phase 1: Extract

**Goal:** Discover exactly what CI ran - the command, environment, and context.

**Step 1: Get the job logs**

Use the existing workflow to retrieve logs for the failed job via `buildkite:get_logs` MCP tool.

**Step 2: Find the actual command**

Look early in the log output for the command execution line. Common patterns:

- **Docker-compose plugin:** `:docker: Running /bin/sh -e -c '<command>' in service <service>`
- **Shell trace:** Lines starting with `+ ` when shell trace is enabled
- **Direct command steps:** Command appears after "Running command" or similar

**Step 3: Identify environment variables**

Check multiple sources in order:

1. **Log output** - Some pipelines print env vars at job start
2. **Pipeline config** - Check `.buildkite/pipeline.yml` or buildkite-builder DSL for `env:` blocks
3. **Buildkite defaults** - Reference the env vars doc for standard vars like `CI=true`, `BUILDKITE_BRANCH`, etc.
4. **Discover through failure** - If local run fails differently, a missing env var may be the cause

**Step 4: Note the execution context**

Record:

- Was it running in Docker? Which service/image?
- What working directory?
- Any pre-command setup visible in the log?

### Phase 2: Translate

**Goal:** Convert the CI command to something runnable locally.

**Step 1: Try the direct command first**

Take the extracted command and run it as-is in your local environment. This is the simplest path and often works for:

- Test commands (`rspec`, `jest`, etc.)
- Linting/formatting tools
- Simple scripts

**Step 2: If direct fails, try with docker-compose**

When the command ran in a Docker context in CI, replicate that locally:

```bash
docker-compose run <service> <command>
```

For example, if CI showed:
`:docker: Running /bin/sh -e -c 'bin/rspec spec/models/user_spec.rb' in service app`

Try locally:

```bash
docker-compose run app bin/rspec spec/models/user_spec.rb
```

**Step 3: Set relevant environment variables**

If the command behaves differently, add env vars discovered in Extract phase:

```bash
CI=true RAILS_ENV=test bin/rspec spec/models/user_spec.rb
```

Or with docker-compose:

```bash
docker-compose run -e CI=true -e RAILS_ENV=test app bin/rspec ...
```

**Step 4: Handle common translation patterns**

- Parallelization flags that need adjustment for local (e.g., `--parallel 4` → `--parallel 1`)
- CI-only flags to remove (e.g., `--format buildkite`)
- Artifact paths that differ locally

### Phase 3: Triage

**Goal:** When local reproduction isn't feasible, determine the best alternative approach.

**Decision point: Can this be reproduced locally?**

Local reproduction is likely NOT feasible when:

- Command needs infrastructure not available locally (specific databases, internal APIs, secrets)
- Environment differences are too significant to bridge (specific Linux dependencies, network topology)
- The failure is tied to CI-specific state (parallelization across agents, artifact dependencies from earlier steps)

Note: Many Buildkite plugins don't affect local reproduction - plugins for artifacts, notifications, or caching are CI orchestration concerns, not execution blockers.

**Alternative 1: Trigger a test build with debugging changes**

Push a branch with modifications to aid debugging:

- Add verbose flags to the failing command
- Insert `echo` statements or print debugging
- Add env var dumping to the pipeline/script
- Modify environment variables in pipeline config
- Temporarily simplify the command to isolate the issue

**Alternative 2: Inspect artifacts**

Download artifacts from the failed build using `buildkite:list_artifacts` MCP tool:

- Test output files (JUnit XML, coverage reports)
- Log files written during execution
- Screenshots or other debug outputs

**Alternative 3: Analyze the failure in place**

Sometimes reproduction isn't needed - the logs plus artifacts contain enough information to understand and fix the issue without running it locally.

## Integration Points

- Existing "Step 6: Help reproduce locally" in the "Investigating a Build from URL" workflow becomes a pointer to this new comprehensive workflow
- The new workflow assumes you've already completed investigation steps 1-5 (getting build info, identifying failed jobs, retrieving logs)

## New Reference Document

Create `references/buildkite-environment-variables.md` with content pulled from https://buildkite.com/docs/pipelines/configure/environment-variables

This provides a local reference for standard Buildkite environment variables (`CI`, `BUILDKITE_*`, etc.) without requiring a web fetch during debugging.

## Implementation Tasks

1. Rename skill directory from `monitoring-buildkite-builds` to `working-with-buildkite-builds`
2. Update SKILL.md frontmatter (name, description)
3. Add new "Reproducing Build Failures Locally" workflow section
4. Update "Step 6" in existing investigation workflow to reference new workflow
5. Fetch and create `references/buildkite-environment-variables.md`
6. Update plugin manifest if needed
