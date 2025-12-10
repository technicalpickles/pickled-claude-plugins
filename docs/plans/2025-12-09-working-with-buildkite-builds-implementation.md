# Working with Buildkite Builds - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rename monitoring-buildkite-builds to working-with-buildkite-builds and add a workflow for reproducing build failures locally.

**Architecture:** Rename skill directory, update frontmatter, add new workflow section to SKILL.md, create new reference document for Buildkite environment variables.

**Tech Stack:** Markdown, Git

---

## Task 1: Rename Skill Directory

**Files:**
- Rename: `plugins/ci-cd-tools/skills/monitoring-buildkite-builds/` → `plugins/ci-cd-tools/skills/working-with-buildkite-builds/`

**Step 1: Rename the directory using git mv**

```bash
cd /Users/josh.nichols/workspace/pickled-claude-plugins/.worktrees/working-with-buildkite-builds
git mv plugins/ci-cd-tools/skills/monitoring-buildkite-builds plugins/ci-cd-tools/skills/working-with-buildkite-builds
```

**Step 2: Verify the rename**

```bash
ls plugins/ci-cd-tools/skills/
```

Expected: `developing-buildkite-pipelines  working-with-buildkite-builds`

**Step 3: Commit**

```bash
git add -A
git commit -m "refactor(ci-cd-tools): rename monitoring-buildkite-builds to working-with-buildkite-builds"
```

---

## Task 2: Update SKILL.md Frontmatter

**Files:**
- Modify: `plugins/ci-cd-tools/skills/working-with-buildkite-builds/SKILL.md:1-4`

**Step 1: Update the frontmatter name and description**

Change from:
```yaml
---
name: buildkite-status
description: Use when checking Buildkite CI status for PRs, branches, or builds - provides workflows for monitoring build status, investigating failures, and handling post-push scenarios with progressive detail disclosure. Use when tempted to use GitHub tools instead of Buildkite-native tools, or when a Buildkite tool fails and you want to fall back to familiar alternatives.
---
```

To:
```yaml
---
name: working-with-buildkite-builds
description: Use when working with Buildkite CI - checking status, investigating failures, and reproducing issues locally. Provides workflows for monitoring builds, progressive failure investigation, and local reproduction strategies. Use when tempted to use GitHub tools instead of Buildkite-native tools, or when a Buildkite tool fails and you want to fall back to familiar alternatives.
---
```

**Step 2: Update the H1 title**

Change from:
```markdown
# Buildkite Status
```

To:
```markdown
# Working with Buildkite Builds
```

**Step 3: Update the Overview section**

Change from:
```markdown
## Overview

This skill provides workflows and tools for checking and monitoring Buildkite CI status. It focuses on **checking status and investigating failures** rather than creating or configuring pipelines. Use this skill when working with Buildkite builds, especially for PR workflows, post-push monitoring, and failure investigation.
```

To:
```markdown
## Overview

This skill provides workflows and tools for working with Buildkite CI builds. It covers **checking status, investigating failures, and reproducing issues locally** rather than creating or configuring pipelines. Use this skill when working with Buildkite builds, especially for PR workflows, post-push monitoring, failure investigation, and local reproduction.
```

**Step 4: Commit**

```bash
git add plugins/ci-cd-tools/skills/working-with-buildkite-builds/SKILL.md
git commit -m "refactor(ci-cd-tools): update skill name and description to working-with-buildkite-builds"
```

---

## Task 3: Update Step 6 Reference in Investigation Workflow

**Files:**
- Modify: `plugins/ci-cd-tools/skills/working-with-buildkite-builds/SKILL.md` (around line 179-186)

**Step 1: Find and update Step 6 in "Investigating a Build from URL" workflow**

Locate the current Step 6:
```markdown
**Step 6: Help reproduce locally**

Based on the error, suggest:

- Which tests to run locally
- Environment setup needed
- Commands to reproduce the failure
```

Replace with:
```markdown
**Step 6: Reproduce locally**

Follow the "Reproducing Build Failures Locally" workflow below to:

1. Extract the exact command CI ran
2. Translate it to a local equivalent
3. Triage if local reproduction isn't feasible

See the dedicated workflow section for detailed steps.
```

**Step 2: Commit**

```bash
git add plugins/ci-cd-tools/skills/working-with-buildkite-builds/SKILL.md
git commit -m "docs(ci-cd-tools): update Step 6 to reference new reproduction workflow"
```

---

## Task 4: Add Reproducing Build Failures Locally Workflow

**Files:**
- Modify: `plugins/ci-cd-tools/skills/working-with-buildkite-builds/SKILL.md` (insert after "### 6. Checking Blocked Builds" section, before "## Understanding Buildkite States")

**Step 1: Add the new workflow section**

Insert the following after the "### 6. Checking Blocked Builds" section (around line 448):

```markdown
### 7. Reproducing Build Failures Locally

After investigating a failed build (workflows 1-2), use this workflow to reproduce the failure locally for debugging.

#### Phase 1: Extract

**Goal:** Discover exactly what CI ran - the command, environment, and context.

**Step 1: Get the job logs**

Use workflow "### 2. Retrieving Job Logs" to get logs for the failed job.

**Step 2: Find the actual command**

Look early in the log output for the command execution line. Common patterns:

- **Docker-compose plugin:** `:docker: Running /bin/sh -e -c '<command>' in service <service>`
- **Shell trace:** Lines starting with `+ ` when shell trace is enabled
- **Direct command steps:** Command appears after "Running command" or similar

Example log snippet:
```
Running plugin docker-compose command hook
:docker: Found a pre-built image for app
:docker: Creating docker-compose override file for prebuilt services
:docker: Pulling services app
:docker: Starting dependencies
:docker: Running /bin/sh -e -c 'bin/rspec spec/models/user_spec.rb' in service app
```

The actual command here is `bin/rspec spec/models/user_spec.rb`.

**Step 3: Identify environment variables**

Check multiple sources in order:

1. **Log output** - Some pipelines print env vars at job start
2. **Pipeline config** - Check `.buildkite/pipeline.yml` or buildkite-builder DSL for `env:` blocks
3. **Buildkite defaults** - See [references/buildkite-environment-variables.md](references/buildkite-environment-variables.md) for standard vars like `CI=true`, `BUILDKITE_BRANCH`, etc.
4. **Discover through failure** - If local run fails differently, a missing env var may be the cause

**Step 4: Note the execution context**

Record:

- Was it running in Docker? Which service/image?
- What working directory?
- Any pre-command setup visible in the log?

#### Phase 2: Translate

**Goal:** Convert the CI command to something runnable locally.

**Step 1: Try the direct command first**

Run the extracted command as-is in your local environment:

```bash
bin/rspec spec/models/user_spec.rb
```

This often works for:
- Test commands (`rspec`, `jest`, `pytest`, etc.)
- Linting/formatting tools
- Simple scripts

**Step 2: If direct fails, try with docker-compose**

When the command ran in a Docker context in CI, replicate that locally:

```bash
docker-compose run <service> <command>
```

Example - if CI showed:
`:docker: Running /bin/sh -e -c 'bin/rspec spec/models/user_spec.rb' in service app`

Try locally:
```bash
docker-compose run app bin/rspec spec/models/user_spec.rb
```

**Step 3: Set relevant environment variables**

If the command behaves differently, add env vars discovered in Phase 1:

```bash
CI=true RAILS_ENV=test bin/rspec spec/models/user_spec.rb
```

Or with docker-compose:
```bash
docker-compose run -e CI=true -e RAILS_ENV=test app bin/rspec spec/models/user_spec.rb
```

**Step 4: Handle common translation patterns**

| CI Pattern | Local Translation |
|------------|-------------------|
| `--parallel 4` | `--parallel 1` or remove flag |
| `--format buildkite` | `--format progress` or remove flag |
| CI-specific artifact paths | Use local paths |
| `buildkite-agent artifact download` | Download manually or skip |

#### Phase 3: Triage

**Goal:** When local reproduction isn't feasible, determine the best alternative.

**Decision: Can this be reproduced locally?**

Local reproduction is likely **NOT feasible** when:

- Command needs infrastructure not available locally (specific databases, internal APIs, secrets)
- Environment differences are too significant (specific Linux dependencies, network topology)
- Failure is tied to CI-specific state (parallelization across agents, artifact dependencies from earlier steps)

**Note:** Many Buildkite plugins don't block local reproduction - plugins for artifacts, notifications, or caching are CI orchestration concerns, not execution blockers.

**Alternative 1: Trigger a test build with debugging changes**

Push a branch with modifications to aid debugging:

- Add verbose flags to the failing command (e.g., `--verbose`, `-vvv`)
- Insert `echo` statements or print debugging
- Add env var dumping: `env | sort` or `printenv`
- Modify environment variables in pipeline config
- Temporarily simplify the command to isolate the issue

**Alternative 2: Inspect artifacts**

Download artifacts from the failed build:

```javascript
mcp__MCPProxy__call_tool('buildkite:list_artifacts', {
  org_slug: '<org>',
  pipeline_slug: '<pipeline>',
  build_number: '<build-number>',
});
```

Look for:
- Test output files (JUnit XML, coverage reports)
- Log files written during execution
- Screenshots or other debug outputs

**Alternative 3: Analyze the failure in place**

Sometimes reproduction isn't needed - the logs plus artifacts contain enough information to understand and fix the issue without running it locally.
```

**Step 2: Commit**

```bash
git add plugins/ci-cd-tools/skills/working-with-buildkite-builds/SKILL.md
git commit -m "feat(ci-cd-tools): add Reproducing Build Failures Locally workflow"
```

---

## Task 5: Create Buildkite Environment Variables Reference

**Files:**
- Create: `plugins/ci-cd-tools/skills/working-with-buildkite-builds/references/buildkite-environment-variables.md`

**Step 1: Fetch Buildkite environment variables documentation**

Use WebFetch to get content from https://buildkite.com/docs/pipelines/configure/environment-variables

**Step 2: Create the reference document**

Create `references/buildkite-environment-variables.md` with the key environment variables extracted and organized.

The document should include:
- Runtime environment variables (CI, BUILDKITE, BUILDKITE_BRANCH, etc.)
- Build-specific variables (BUILDKITE_BUILD_NUMBER, BUILDKITE_COMMIT, etc.)
- Job-specific variables (BUILDKITE_JOB_ID, BUILDKITE_STEP_KEY, etc.)
- Agent variables (BUILDKITE_AGENT_NAME, etc.)

**Step 3: Commit**

```bash
git add plugins/ci-cd-tools/skills/working-with-buildkite-builds/references/buildkite-environment-variables.md
git commit -m "docs(ci-cd-tools): add Buildkite environment variables reference"
```

---

## Task 6: Update Resources Section

**Files:**
- Modify: `plugins/ci-cd-tools/skills/working-with-buildkite-builds/SKILL.md` (Resources section near end)

**Step 1: Add new reference to Resources section**

Find the References list and add the new document:

```markdown
### References

- **[buildkite-states.md](references/buildkite-states.md)** - Complete guide to Buildkite states...
- **[annotation-patterns.md](references/annotation-patterns.md)** - How different projects use annotations...
- **[tool-capabilities.md](references/tool-capabilities.md)** - Comprehensive capability matrix...
- **[url-parsing.md](references/url-parsing.md)** - Understanding Buildkite URLs...
- **[troubleshooting.md](references/troubleshooting.md)** - Common errors, solutions...
- **[buildkite-environment-variables.md](references/buildkite-environment-variables.md)** - Standard Buildkite environment variables for local reproduction
```

**Step 2: Commit**

```bash
git add plugins/ci-cd-tools/skills/working-with-buildkite-builds/SKILL.md
git commit -m "docs(ci-cd-tools): add environment variables reference to Resources section"
```

---

## Task 7: Validate Plugin

**Step 1: Run plugin validation**

```bash
cd /Users/josh.nichols/workspace/pickled-claude-plugins/.worktrees/working-with-buildkite-builds
claude plugin validate plugins/ci-cd-tools
```

Expected: Validation passes

**Step 2: If validation fails, fix issues and re-commit**

---

## Task 8: Final Review

**Step 1: Review all changes**

```bash
git log --oneline main..HEAD
git diff main --stat
```

**Step 2: Read through the updated SKILL.md to verify coherence**

Ensure:
- Frontmatter is correct
- New workflow section flows logically after existing workflows
- Step 6 reference points to new workflow correctly
- Resources section includes new reference

**Step 3: Report completion**

Summarize what was implemented and any issues encountered.
