# Capturing several sources at once

When the user hands over a batch ("make notes for each of these", "write them up", "atomic notes
for each option/family we found"), dispatch **one subagent per note** so each reads its source in
isolation and cannot cross-contaminate. Default to it for 3+ sources.

Phrasing like "each option", "separate notes", or "at least the families of them" is standing
permission for the whole batch: don't re-ask per item once the batch is agreed. A single new note
still goes through the normal opening (see SKILL.md Step 1).

## What you do

1. Tell each subagent: invoke the `second-brain:capture` skill, follow "Running as a batch
   subagent" in this file, and `$TMPDIR` is `<value of echo $TMPDIR>` (subagents don't inherit it).
2. After all notes exist, do the daily breadcrumbs, the cross-links between the new notes, and the
   closing proposals yourself, since connections need the whole set in view.

## Running as a batch subagent

| Does | Skips | Reports back |
|------|-------|--------------|
| Search, the fetch ladder, create the note, follow the note contract | The why question, showing hits, the breadcrumb, closing proposals, Step 6 | Path, title, verified links, anything unconfirmed, and coverage |

**Coverage** is roughly what share of the source you retrieved, plus any suspected truncation
(a summarizing fetcher cut it short, a page loaded only partly). Say it even when it's 100%.
