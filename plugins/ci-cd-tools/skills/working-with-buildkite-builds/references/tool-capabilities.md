# Tool Capabilities Reference

This document provides complete capability information for all Buildkite status checking tools.

## Overview

Three tool categories exist with different strengths and limitations:

1. **bktide CLI** - Primary tool, especially `snapshot` command for comprehensive build investigation
2. **MCP Tools** - Direct Buildkite API access via Model Context Protocol (fallback, programmatic access)
3. **Bundled Scripts** - Legacy helper wrappers (mostly superseded by bktide snapshot)

## Capability Matrix

| Capability            | bktide snapshot     | bktide CLI          | MCP Tools                       | Notes                          |
| --------------------- | ------------------- | ------------------- | ------------------------------- | ------------------------------ |
| Parse any BK URL      | ✅                  | ❌                  | ❌                              | snapshot handles URL parsing   |
| List pipelines        | ❌                  | ✅ `pipelines`      | ✅ `buildkite:list_pipelines`   |                                |
| List builds           | ❌                  | ✅ `builds`         | ✅ `buildkite:list_builds`      |                                |
| Get build details     | ✅ (build.json)     | ✅ `build`          | ✅ `buildkite:get_build`        |                                |
| Get annotations       | ✅ (annotations.json) | ✅ `annotations`  | ✅ `buildkite:list_annotations` |                                |
| **Retrieve job logs** | **✅** (steps/*/log.txt) | **❌**         | **✅ `buildkite:get_logs`**     | snapshot captures automatically |
| Save to files         | ✅                  | ❌                  | ❌                              | For later analysis             |
| List artifacts        | ❌                  | ❌                  | ✅ `buildkite:list_artifacts`   |                                |
| Wait for build        | ❌                  | ❌                  | ✅ `buildkite:wait_for_build`   |                                |
| Unblock jobs          | ❌                  | ❌                  | ✅ `buildkite:unblock_job`      |                                |
| Human-readable output | ✅                  | ✅                  | ❌ (JSON)                       |                                |

## Detailed Tool Information

### MCP Tools (Fallback / Programmatic Access)

**Access Method:** `mcp__MCPProxy__call_tool("buildkite:<tool>", {...})`

**Authentication:** Configured in MCP server settings (typically uses `BUILDKITE_API_TOKEN`)

**When to use:**
- bktide not available
- Need `wait_for_build` (polling until completion)
- Need `unblock_job` (manual approval steps)
- Programmatic/automated workflows

**Key Tools:**

#### `buildkite:get_build`

Get detailed build information including job states, timing, and metadata.

Parameters:

- `org_slug` (required): Organization slug
- `pipeline_slug` (required): Pipeline slug
- `build_number` (required): Build number
- `detail_level` (optional): "summary" | "detailed" | "complete"
- `job_state` (optional): Filter jobs by state ("failed", "passed", etc.)

Returns: Build object with jobs array, state, timing, author, etc.

#### `buildkite:get_logs`

**THE CRITICAL TOOL** - Retrieve actual log output from a job.

Parameters:

- `org_slug` (required): Organization slug
- `pipeline_slug` (required): Pipeline slug
- `build_number` (required): Build number
- `job_id` (required): Job UUID (NOT step ID from URL)

Returns: Log text content

**Common Issues:**

- "job not found" → Using step ID instead of job UUID
- Empty response → Job hasn't started or finished yet

#### `buildkite:wait_for_build`

Poll build until completion.

Parameters:

- `org_slug` (required): Organization slug
- `pipeline_slug` (required): Pipeline slug
- `build_number` (required): Build number
- `timeout` (optional): Seconds until timeout (default: 1800)
- `poll_interval` (optional): Seconds between checks (default: 30)

Returns: Final build state when complete or timeout

### bktide CLI (Primary)

**Access Method:** `npx bktide@latest <command>`

**Authentication:** `BK_TOKEN` environment variable or `~/.bktide/config`

**Key Commands:**

#### `snapshot` (Preferred for Investigations)

```bash
npx bktide@latest snapshot <buildkite-url>     # Capture build with failed/broken steps
npx bktide@latest snapshot --all <url>         # Capture all steps including passing
```

Takes any Buildkite URL (build URL, step URL, etc.) and saves:
- `manifest.json` - Step index with states and exit codes
- `build.json` - Full build metadata
- `annotations.json` - Build annotations
- `steps/<id>/log.txt` - Log for each captured step
- `steps/<id>/step.json` - Step metadata

Output location: `./tmp/bktide/snapshots/<org>/<pipeline>/<build>/`

#### Other Commands

```bash
npx bktide@latest pipelines <org>                    # List pipelines
npx bktide@latest builds <org>/<pipeline>            # List recent builds
npx bktide@latest build <org>/<pipeline>#<number>    # Build details
npx bktide@latest annotations <org>/<pipeline>#<number>    # Show annotations
```

### Bundled Scripts (Tertiary)

**Access Method:** `~/.claude/skills/buildkite-status/scripts/<script>.js`

**Authentication:** Use bktide internally (requires `BK_TOKEN`)

**Pros:**

- Purpose-built for specific workflows
- Handle common use cases automatically
- Provide structured output

**Cons:**

- Depend on bktide (external dependency)
- Limited to specific use cases
- May have version compatibility issues

**Available Scripts:**

#### `find-commit-builds.js`

Find builds matching a specific commit SHA.

Usage:

```bash
~/.claude/skills/buildkite-status/scripts/find-commit-builds.js <org> <commit-sha>
```

Returns: JSON array of matching builds

#### `wait-for-build.js`

Monitor build until completion (background-friendly).

Usage:

```bash
~/.claude/skills/buildkite-status/scripts/wait-for-build.js <org> <pipeline> <build> [options]
```

Options:

- `--timeout <seconds>`: Max wait time (default: 1800)
- `--interval <seconds>`: Poll interval (default: 30)

Exit codes:

- 0: Build passed
- 1: Build failed
- 2: Build canceled
- 3: Timeout

#### `get-build-logs.js` (NEW - to be implemented)

Retrieve logs for a failed job with automatic UUID resolution.

Usage:

```bash
~/.claude/skills/buildkite-status/scripts/get-build-logs.js <org> <pipeline> <build> <job-label-or-uuid>
```

Features:

- Accepts job label or UUID
- Automatically resolves label → UUID
- Handles step ID confusion
- Formats output for readability

## Decision Matrix: Which Tool to Use

### Use `bktide snapshot` When:

- Investigating a build failure (most common case)
- Given a Buildkite URL to analyze
- Need to review logs from multiple steps
- Want everything saved to files for analysis

### Use other bktide commands When:

- Listing pipelines or builds
- Getting quick status overview
- Interactive terminal work

### Use MCP Tools When:

- Waiting for a build to complete (`wait_for_build`)
- Unblocking manual approval steps (`unblock_job`)
- bktide not available
- Need programmatic/structured JSON data

## Common Mistakes

### ❌ Not using snapshot for investigations

**Don't**: Manually parse URLs and make multiple API calls

**Do**: `npx bktide@latest snapshot <url>` - handles everything automatically

### ❌ Using step ID for MCP log retrieval

**Don't**: Extract `sid=019a5f...` from URL and use with `get_logs`

**Why**: Step IDs ≠ Job UUIDs. MCP tools need job UUIDs.

**Do**: Use `bktide snapshot` (handles this automatically), or call `get_build` to get job UUIDs

### ❌ Falling back to GitHub tools

**Don't**: "bktide failed, I'll use `gh pr view` instead"

**Why**: GitHub only shows summaries, loses critical information.

**Do**: Try MCP tools as fallback, or fix bktide issue

## Troubleshooting

### Issue: "job not found" when calling get_logs

**Diagnosis**: Using step ID instead of job UUID

**Solution**:

1. Call `buildkite:get_build` with `detail_level: "detailed"`
2. Find job by `label` field
3. Extract `uuid` field
4. Use that UUID in `get_logs` call

### Issue: bktide command not found

**Diagnosis**: npm/npx not installed or not in PATH

**Solution**:

1. Use MCP tools instead (preferred)
2. Or install: `npm install -g @anthropic/bktide`

### Issue: Empty logs returned

**Diagnosis**: Job hasn't completed or logs not available yet

**Solution**:

1. Check job `state` - should be terminal (passed/failed/canceled)
2. Wait for job to finish
3. Check job `started_at` and `finished_at` timestamps

## See Also

- [SKILL.md](../SKILL.md) - Main skill documentation
- [troubleshooting.md](troubleshooting.md) - Common errors and solutions
- [url-parsing.md](url-parsing.md) - Understanding Buildkite URLs
