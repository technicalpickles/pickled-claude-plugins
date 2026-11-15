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
  - Bash(${CLAUDE_PLUGIN_ROOT}/scripts/survey-inbox.py)
  - Bash(which:qmd)
  - Bash(qmd:query *)
  - Bash(qmd:collection list)
  - Bash(qmd:get *)
  - Bash(qmd:status)
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python3 \"${CLAUDE_PLUGIN_ROOT}\"/hooks/check-sb-before-call.py"
---

# Process Inbox

Process accumulated inbox notes through the full pipeline: ingest, enrich, route, connect, link to daily note.

See `../obsidian/references/pipeline.md` for stage definitions and status flow.

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
- `../obsidian/references/pipeline.md` for stage definitions
- `../obsidian/references/routing-memory.md` for learning loop
- `../obsidian/references/routing.md` for scoring algorithm
- `../obsidian/references/connecting.md` for connection discovery
- `../obsidian/references/daily-linking.md` for daily note linking
- `../obsidian/references/sb-cli.md` for sb command reference

## Step 2: Survey Inbox

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/survey-inbox.py
```

It reads every note in the default vault's inbox and prints JSON. Each note
is in exactly one bucket of `next`:

| Bucket | Notes | What happens |
|--------|-------|--------------|
| `ingest`, `enrich`, `route`, `connect`, `link-daily` | Pipeline status (`raw` session notes, `ingested`, `enriched` or `pending-review`, `routed`, `connected`) | That stage in Step 3 |
| `kept-record` | A session note `ingest` split up, kept as a record | Nothing |
| `route-keep-status` | A vault status (`seedling`, `filed`, `active`, ...) or no status on a note that isn't a session note: a finished note sitting in the inbox | Step 3c, keeping its status |
| `empty` | Title only, no body | Ask: delete or fill in. Never process |
| `session-not-on-disk` | Raw session note naming a Claude Code session whose transcript isn't on this machine, or whose session id is malformed | Leave it untouched |
| `unknown-status` | A status in none of the vocabularies, or `raw` on a note that isn't a session note | Ask, after checking the vault CLAUDE.md's status vocabulary |

`stale` lists notes captured more than 14 days ago. `near_duplicates` lists
pairs of notes where one title's words all appear in the other's.

Why the status buckets: `status` carries pipeline state, zettelkasten
maturity and vault lifecycle in one key. See "Status Values" in
`../obsidian/references/pipeline.md`.

Present summary:

```
Inbox: {total} notes
  {n} to ingest (session notes)
  {n} to enrich
  {n} to route ({k} pipeline, {m} finished notes keeping their status)
  {n} to connect
  {n} to link to the daily note

{If session-not-on-disk:}
  Holding {n} session notes whose sessions aren't on this machine
  ({repos}). Process them on the machine that wrote them, or after syncing.
{If empty:}
  {n} empty notes: {filenames}. Delete, or leave for you to fill in?
{If near_duplicates:}
  Possible duplicates: {each pair}. Compare before routing?
{If unknown-status:}
  {n} notes with a status I don't recognize: {filename: status}.
{If stale:}
  Heads up: {n} notes have been in the inbox for over 2 weeks.
```

Ask the empty-note and duplicate questions in this one message and wait
for the answers before Step 3. Delete the empty notes the user says to
delete; the rest stay out of Step 3. Merge the duplicates the user says to
merge: keep the fuller note, fold the other's unique content into it, and
delete the other. Duplicates the user keeps apart go through Step 3 as
usual.

If inbox is empty:
```
Inbox is empty. Nothing to process.
```

If the `route` and `route-keep-status` buckets hold more than about 20
notes between them, use
[Large backlogs](#large-backlogs) for the rest of the run.

## Step 3: Process by Stage

Work through notes in pipeline order. Each stage picks up notes at its expected input status.

### 3a: Ingest raw session notes

For each note in the `ingest` bucket:
- Follow the `ingest` skill (keeps the note whole by default, only splits
  on a real cross-topic signal)
- Report: `Ingested: {session filename}` (default case), or
  `Ingested: {session filename} -> {n} insights (split)` (exception case)

### 3b: Enrich ingested insights

For each note with `status: ingested` and `type: insight`:
- Follow the `enrich` skill to create proper zettelkasten notes
- Report: `Enriched: {filename}`

### 3c: Route enriched notes and finished notes

For each note in the `route` and `route-keep-status` buckets:
- Follow the `route` skill. For a `route-keep-status` note, route never
  writes `routed` or `pending-review`: it moves the note or leaves it, and
  its status stays as it is.
- If auto-routed: `Routed: {filename} -> {destination}`
- If pending-review: pause and present suggestions to user
  - Show the note title, top destinations with scores, and reasoning
  - Let user pick destination or leave in inbox
  - If user overrides, capture correction per `../obsidian/references/routing-memory.md`
  - After user decides, continue to next note

Also process any pre-existing `pending-review` notes from previous runs.

### 3d: Connect routed notes

For each note with `status: routed`, plus each `route-keep-status` note
this run moved that has no `## Related` section yet (capture already
connected the ones that do):
- Follow the `connect` skill, without writing a status to the
  `route-keep-status` notes
- If qmd unavailable: `Skipped connections: qmd not available` (once, not per note)
- If connections found: present batch summary, let user multi-select
- If no connections: skip silently

### 3e: Link to daily note

For each note with `status: connected`, plus the `route-keep-status`
notes this run moved:
- Follow the `link-daily` skill, without writing a status to the
  `route-keep-status` notes
- Batch all links into a single `sb daily append` call when possible
- Report: `Linked {n} notes to daily note`

## Step 4: Summary

```
Pipeline complete:
  {n} session notes ingested ({s} kept whole, {m} insights extracted from splits)
  {n} insights enriched
  {n} notes routed ({auto} auto, {manual} manual)
  {n} notes connected ({links} links added)
  {n} notes linked to daily note
  {n} notes still pending review
  {n} session notes held (sessions not on this machine)
  {n} empty notes deleted, {n} left
```

## Large backlogs

The per-note questions in Step 3 stop working past a couple dozen notes.
Switch to this mode when the survey's `route` and `route-keep-status`
buckets hold more than about 20 notes between them, or when the user asks
to clear a big backlog:

1. **Work in chunks of about 20 notes**, in the survey's order (oldest
   first). Status is written per note, so a run can stop after any chunk
   and the next run picks up where it left off. Say how many are left
   after each chunk.
2. **Route by cluster, not by note.** Group the chunk's routing candidates
   by their top destination. Auto-route what clears the threshold as
   usual, then ask once per cluster: "These 6 look like `67 Dev tools`:
   {titles}. Route them all there?" with "route all", "pick some", and
   "leave in inbox". A cluster answer that overrides the suggestion is one
   correction in `.routing-memory.md`, not one per note.
3. **Connect without asking per note.** Add confident links (same subject,
   or named in the note) the way `capture` does, and list the weaker
   candidates in the chunk summary instead of asking about each one.
4. **Summarize each chunk** in a few lines: routed where, links added,
   what is still pending. Ask only what blocks the next chunk.

## Constraints

- Process stages in order (ingest before enrich, enrich before route, etc.)
- Pause for human input only on low-confidence routing and connection selection,
  and on the survey's empty-note and duplicate questions
- Never write a pipeline status over a vault status. See "Status Values" in
  `../obsidian/references/pipeline.md`
- Don't fail the pipeline if one stage errors on a note. Log the error and continue.
- Batch operations where possible (daily linking)
- One vault at a time (uses default vault)
