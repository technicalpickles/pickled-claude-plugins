---
name: vault-capture
description: Use when Josh asks to write a note, make a note, or capture something for his "pickled-knowledge" Obsidian vault - triggers on "write a note about X", "make a note for this", "capture this", "note this up", "put together a note on X", or a bare URL/article/tweet handed over with intent to write it up. Do NOT use for generic writing help, drafting prose that isn't a vault note, or when Josh is just asking a question and not asking for a note.
---

# Vault Capture

Turn a source (or a raw idea) into one Obsidian note file, already shaped for Josh's
`pickled-knowledge` vault - correct filename, correct frontmatter, correct body shape, and a
best-guess at where it'll eventually live. He should be able to save the file straight into his
vault with no renaming, no reformatting, no hunting down the source URL after the fact.

This is a chat-only rewrite of a more capable version that runs inside Claude Code (searches
the vault first, checks for duplicates, auto-links related notes, appends a daily-note
breadcrumb, actually files the note). None of that is reachable from here - no filesystem, no
vault search index. Say so plainly once, up front, rather than quietly skipping it:

> "Heads up: I can't search your vault from here, so I'm not checking for an existing note or
> suggesting related links - worth a quick check yourself before you file this."

## Step 1: Get the real source - never invent one

- **A URL was given:** fetch and read it for real (browse it). Never write the note from the
  URL text alone, a guess at what the page probably says, or general knowledge about the
  topic. If the page can't be reached, say so and stop - don't write a plausible-sounding note
  anyway.
- **A tweet/thread:** read the actual tweet content if it can be fetched. If not reachable,
  say so rather than reconstructing it from context.
- **No URL, just an idea or topic:** there is no source to fetch. Don't backfill one from
  training knowledge and present it as researched. Write the note from what Josh actually said,
  and leave `source` off the frontmatter entirely.
- **Several sources at once** ("make notes for each of these"): handle them one at a time, in
  order, and produce one file per source. There's no subagent fan-out available here.

## Step 2: Write the frontmatter

```yaml
---
status: seedling
tags: [lowercase, hyphenated, no-leading-hash]
created: 2026-09-11
source: https://example.com/the-actual-page
---
```

- **`status: seedling`** always, for a fresh capture. This is the note's maturity, not a
  workflow state - don't write `filed`, `active`, `incubating`, etc. Those belong to notes
  that have already been routed inside the vault, which this one hasn't.
- **`tags`**: a short list, lowercase, hyphenated, **no `#` prefix** (a bare `#` at the start
  of a YAML flow-sequence item is a comment and silently corrupts the frontmatter). Pick 2-4
  topic tags from what the note is actually about. [references/jd-map.md](references/jd-map.md)
  is useful here too - a tag that matches how the vault already splits a topic (e.g. `ruby` vs
  a generic `programming`) ages better.
- **`created`**: today's date, `YYYY-MM-DD`.
- **`source`**: the real URL/origin actually fetched in Step 1. Omit the field entirely for a
  sourceless idea capture - don't write `source: none` or similar.

## Step 3: Write the body

```markdown
# Glide browser

A [Firefox fork](https://glide-browser.app/firefox) that is keyboard-focused, with a
Vim-style modal interface and a TypeScript config surface.
```

- **`# Title`** in sentence case, matching the source's own framing rather than a generic
  topic label - `# Glide browser`, not `# Notes on a keyboard-driven browser`.
- **Prose, not an outline.** One to three paragraphs. Only reach for `##` subheadings once
  there's enough content to need them - a three-paragraph note doesn't need five headings.
- **Link out inline** to the primary source so the reader can get to the real thing.
- **No `## Related` section.** The real vault workflow only links to notes a live search
  confirmed exist; nothing here can confirm that, so don't fabricate `[[wiki-links]]` to
  notes that may or may not exist. Leave that entirely to Josh.
- **One note, one idea.** If the source clearly carries several distinct, separable ideas,
  say so and offer to split it into multiple notes rather than writing one sprawling one.

## Step 4: Name the file

```
202609111420 glide-browser.md
└──┬───────┘ └──────┬──────┘
   │                └─ hyphenated slug, from the title
   └─ YYYYMMDDHHMM, then a single SPACE (not a hyphen)
```

Use the current date and time (down to the minute, best effort). The space between the
timestamp and the slug is exactly one space - a hyphen there (`202608071430-glide-browser.md`)
is the wrong shape.

## Step 5: Guess a likely destination

Read [references/jd-map.md](references/jd-map.md) - the vault's Johnny Decimal area map - and
name the area/category the note will probably land in once routed (e.g. "probably `66 AI &
agentic development`"). This is Josh's own filing step to do, not something happening here -
frame it as a guess he can accept or override, never as a decision already made. Say so plainly
when two areas are plausible, or when nothing fits well.

## Step 6: Hand over the file

Create the actual `.md` file (frontmatter + body from Steps 2-3) named exactly as in Step 4,
and give it to Josh as a download. Don't just print the content and ask him to save it himself.

Then, in a few short lines, tell him:
- the filename
- that it's built to drop straight into `10-19 System & Capture/11 Inbox & triage/` in the
  vault (that's where fresh captures land before routing) - he still has to move it there
  himself, nothing here can write into the vault directly
- the likely-destination guess from Step 5
- the one-line duplicate/related-notes caveat from Step 1, if it wasn't already said

No further ceremony - a few short lines are enough, not a summary of every step taken.

## Constraints

- **Never fabricate.** No invented URLs, no filled-in details from memory, no `[[links]]` to
  notes that might not exist. If the source can't be reached, say that and stop.
- **No workflow-state values.** Fresh captures are always `status: seedling`. Leave lifecycle
  status (`filed`, `active`, `incubating`, ...) to whatever actually routes the note later.
- **No pretending to search the vault, and no pretending the destination guess is final.**
  State both limitations plainly and move on.
- **Filename and frontmatter exactly as specified above.** This is the whole point of the
  skill - if Josh still has to rename the file or fix the frontmatter afterward, it failed at
  its one job.
