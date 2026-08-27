---
name: ingest
description: Turn a raw session notes file into an ingested note, ready for the enrich stage. Defaults to keeping it whole; only splits when bullets show a real cross-topic signal. Stage 1 of the processing pipeline.
allowed-tools:
  - Read(~/.claude/vaults/**/*.md)
  - Write(~/.claude/vaults/**/*.md)
  - Edit(~/.claude/vaults/**/*.md)
  - Bash(npx @techpickles/sb:*)
---

# Ingest Stage

Turn a raw session notes file (type: `session-notes`) into an ingested
insight, ready for the `enrich` stage. Defaults to keeping it as one
note — see "Exception" below for when to split.

See `references/pipeline.md` for stage definitions and status flow.

## Input

A session notes file in the inbox with `status: raw` and `type: session-notes`.

## Default: enrich whole

Most session notes — including every `devlog`-produced one — are already
well-organized: one session, one provenance (repo/branch/bean), a handful
of related bullets. Splitting them into N separate notes mints
near-duplicate notes that mostly route to the same destination anyway — a
real run against 32 session notes would have exploded into 120-140
near-duplicates that mostly filed to the same destination.

Default behavior: keep the session note as ONE note. Change its
frontmatter in place, using the Edit tool:
- `status: raw` → `status: ingested`
- `type: session-notes` → `type: insight`

Don't create any new files. Don't touch the body — `enrich` handles prose
cleanup next.

## Exception: split when bullets genuinely diverge

Check for a real cross-topic signal before splitting — not a bullet count.
Read the note's bullets:

- If every bullet shares the same repo/branch/bean context (the common
  case, and always true for a single `devlog` session), keep it whole.
- If bullets explicitly reference **different** repos, branches, or beans
  within the same file (only possible in hand-authored or legacy
  multi-topic session notes — `devlog` output never does this), split
  those bullets into separate notes instead:

  There's no structured per-bullet frontmatter for this — repo/branch/bean
  only ever exist once, at the file level. Infer divergence from what the
  bullet text itself says (e.g. a bullet's prose names a different repo
  than the file's own frontmatter, or than another bullet).

  1. For each insight, create a new note via
     `sb note create --source auto --title "{insight title}"` with
     `status: ingested`, `type: insight`, `source-session: {original session filename}`,
     and that bullet's own repo/branch/bean.
  2. Write the note body (the bullet text, cleaned into a sentence or
     short paragraph) using the Write tool.
  3. Update the original session file's status to `ingested` using the
     Edit tool — it stays in the inbox as a record, not processed
     further.
  4. Skip empty or trivial bullets when splitting (single words,
     fragments).

## Output

Either:
- The same note, now `status: ingested` and `type: insight` (default
  case), or
- N new insight notes with `status: ingested`, plus the original session
  file updated to `status: ingested` (split case)

## Constraints

- Default to whole. Splitting is the exception, not the rule.
- Preserve all provenance metadata.
- Each split-out note gets its own zettelkasten timestamp (via sb).
