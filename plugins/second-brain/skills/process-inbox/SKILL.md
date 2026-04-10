---
name: process-inbox
description: Process accumulated inbox notes through the full pipeline (ingest, enrich, route, connect, link). User-facing orchestrator.
allowed-tools:
  - Read(~/.claude/vaults/**/CLAUDE.md)
  - Read(~/.claude/vaults/**/.obsidian/*.json)
  - Read(~/.claude/vaults/**/*.md)
  - Read(~/.claude/vaults/**/.routing-memory.md)
  - Write(~/.claude/vaults/**/*.md)
  - Write(~/.claude/vaults/**/.routing-memory.md)
  - Edit(~/.claude/vaults/**/*.md)
  - Edit(~/.claude/vaults/**/.routing-memory.md)
  - Bash(npx @techpickles/sb:*)
  - Bash(which:qmd)
  - Bash(qmd:query *)
  - Bash(qmd:collection list)
  - Bash(qmd:get *)
  - Bash(qmd:status)
---

# Process Inbox

Process accumulated inbox notes through the full pipeline: ingest, enrich, route, connect, link to daily note.

See `references/pipeline.md` for stage definitions and status flow.

## Step 1: Load Configuration

```bash
npx @techpickles/sb config default
npx @techpickles/sb config vaults
```

If no vault configured:
```
Second brain not configured. Run /second-brain:setup first.
```

Load skill references:
- `second-brain:obsidian` for tool mechanics
- `references/pipeline.md` for stage definitions
- `references/routing-memory.md` for learning loop
- `references/routing.md` for scoring algorithm
- `references/connecting.md` for connection discovery
- `references/daily-linking.md` for daily note linking
- `references/sb-cli.md` for sb command reference

## Step 2: Survey Inbox

```bash
npx @techpickles/sb inbox list --detail
```

Parse the JSON response. Group notes by `status` field (notes without status are `raw`).

Check for stale notes (captured more than 14 days ago based on `captured` frontmatter field).

Present summary:

```
Inbox: {total} notes
  {n} raw (session notes awaiting ingestion)
  {n} ingested (insights awaiting enrichment)
  {n} enriched (notes awaiting routing)
  {n} pending-review (need your input)
  {n} routed (awaiting connection)
  {n} connected (awaiting daily linking)

{If stale notes exist:}
  Heads up: {n} notes have been in the inbox for over 2 weeks.
```

If inbox is empty:
```
Inbox is empty. Nothing to process.
```

## Step 3: Process by Stage

Work through notes in pipeline order. Each stage picks up notes at its expected input status.

### 3a: Ingest raw session notes

For each note with `status: raw` and `type: session-notes`:
- Follow the `ingest` skill to split into individual insight notes
- Report: `Ingested: {session filename} -> {n} insights`

### 3b: Enrich ingested insights

For each note with `status: ingested` and `type: insight`:
- Follow the `enrich` skill to create proper zettelkasten notes
- Report: `Enriched: {filename}`

### 3c: Route enriched notes

For each note with `status: enriched`:
- Follow the `route` skill
- If auto-routed: `Routed: {filename} -> {destination}`
- If pending-review: pause and present suggestions to user
  - Show the note title, top destinations with scores, and reasoning
  - Let user pick destination or leave in inbox
  - If user overrides, capture correction per `references/routing-memory.md`
  - After user decides, continue to next note

Also process any pre-existing `pending-review` notes from previous runs.

### 3d: Connect routed notes

For each note with `status: routed`:
- Follow the `connect` skill
- If qmd unavailable: `Skipped connections: qmd not available` (once, not per note)
- If connections found: present batch summary, let user multi-select
- If no connections: skip silently

### 3e: Link to daily note

For each note with `status: connected`:
- Follow the `link-daily` skill
- Batch all links into a single `sb daily append` call when possible
- Report: `Linked {n} notes to daily note`

## Step 4: Summary

```
Pipeline complete:
  {n} session notes ingested -> {m} insights extracted
  {n} insights enriched
  {n} notes routed ({auto} auto, {manual} manual)
  {n} notes connected ({links} links added)
  {n} notes linked to daily note
  {n} notes still pending review
```

## Constraints

- Process stages in order (ingest before enrich, enrich before route, etc.)
- Pause for human input only on low-confidence routing and connection selection
- Don't fail the pipeline if one stage errors on a note. Log the error and continue.
- Batch operations where possible (daily linking)
- One vault at a time (uses default vault)
