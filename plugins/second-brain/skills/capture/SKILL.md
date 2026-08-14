---
name: capture
description: Use when the user asks to read a source and make a note for it, create or find an atomic note, or check whether a note already exists. Triggers on "read <url> and make a note", "make a note for", "create (or find) an atomic note", "do we have notes about X?", "check if we have a note for", "capture this", "put together a note", "distill this", and on a bare URL/PDF/tweet/thread handed over with intent to write it up. Covers the whole loop as one arc - search the vault first, read the primary source, write the note through the sb CLI, then offer connections. Use inside an Obsidian vault or anywhere a vault is configured. Do NOT use for draining an accumulated inbox backlog (that is process-inbox), for extracting insights from the current conversation (that is distill-conversation), or for routing already-captured notes to their homes (that is route).
allowed-tools:
  - Read
  - Write(~/.claude/vaults/**/*.md)
  - Edit(~/.claude/vaults/**/*.md)
  - Glob
  - Grep
  - Bash(npx @techpickles/sb:*)
  - mcp__qmd__query
  - mcp__qmd__get
  - mcp__qmd__multi_get
  - mcp__qmd__status
---

# Capture

Write a note into the vault from a source the user hands you. One arc, five steps:
**search → read the primary source → create through sb → leave it in the inbox → offer connections.**

This is the dominant vault interaction. Do not decompose it into separate asks; the user saying
"read this and make a note" means all five steps, and the connect step in particular will not
happen unless this skill runs it.

See [references/note-format.md](references/note-format.md) for frontmatter and body shape.
See [../obsidian/references/sb-cli.md](../obsidian/references/sb-cli.md) for the full sb command surface.

## Step 0: Locate the vault

```bash
npx @techpickles/sb vault info
npx @techpickles/sb config qmd-collection
```

Read the vault's own `CLAUDE.md` if you haven't this session. Vault-specific policy (destinations,
status vocabulary, disambiguation rules) overrides the defaults here.

## Step 1: Search before creating - never skip this

Run a `lex` + `vec` pair through the **qmd MCP tools**, not the shell. (`mcp__qmd__query` is the
working path; shelling out to `qmd` hits Metal-init failures under the sandbox.)

```
mcp__qmd__query
  searches: [{type: 'lex', query: '<topic terms>'},
             {type: 'vec', query: '<what the note would say>'}]
  collection: <from sb config qmd-collection>
  intent: '<why you are searching>'
  rerank: false        # CPU-only box, reranking is not worth the latency here
```

Show the user what already exists - **path + score + snippet** - before anything gets written.
Often the right move is extending a note, not minting one. If a result is a strong match, say so
and ask which way to go instead of quietly creating a duplicate.

### When search comes up empty

A miss is not proof the note is absent. In order:

1. **Basename is the stable identity.** Notes get routed between folders constantly. Search the
   basename across the whole vault (`Glob`/`Grep`) before concluding anything is missing.
2. **Check both inboxes.** `10-19 System & Capture/11 Inbox & triage/` and
   `10-19 System & Capture/11 Inbox/` are separate folders with the same JD code. `sb inbox list`
   only reads the first.
3. **The note may genuinely not exist.** Say that plainly and offer to start one.

### When the user says "that isn't the one"

Do **not** re-run the same query with different phrasing, and do not widen `-n` and hope. Ask for
one distinguishing detail (who made it, where they saw it, what it sits next to) and search on
*that* instead. Re-running near-identical searches has burned entire sessions, including the same
lookup failing twice across two separate sessions.

## Step 2: Read the actual primary source

**Never write a note from search snippets.** Fetch the real thing:

| Source | Tool |
|--------|------|
| Web page | `mcp__lightpanda__markdown {url}` preferred; `WebFetch` as fallback |
| Tweet / thread | `xtweet <url-or-id>` (`-q` for quoted chain, `-r` for replies) |
| PDF or local file | `Read` |
| Notion page | `mcp__notiongusto__notion-fetch` |
| Slack thread | the `slack` skill |

**If you cannot reach the source, or cannot find the thing the user described, stop and say so.**
Do not write a note containing a URL you did not load, a title you inferred, or details you filled
in from background knowledge. Reporting "I couldn't find anything matching this" is the correct
outcome and is more useful than a plausible note that is wrong.

## Step 3: Create the note through sb

```bash
npx @techpickles/sb note create --source auto --title "<title>" --dry-run   # check the path first
npx @techpickles/sb note create --source auto --title "<title>"            # returns JSON with path
```

Then write the body at the returned path with `Write`/`Edit`.

**Do not hand-roll the destination path.** sb resolves the inbox, the zettelkasten timestamp, and
the filename slug (`202608141249 note-title.md` - space after the timestamp, hyphens inside the
slug). Hand-rolled `Write` calls are how captures end up in the inbox the pipeline never reads:
as of 2026-08-14 that had orphaned 46 notes, and untangling it took a single 211-message session.

For a title, prefer the source's own framing over a topic label. `# Glide browser` beats
`# Notes on a keyboard-driven browser`.

## Step 4: Leave it in the inbox - routing is opt-in

The note stays where sb put it. **Offer** to route it; do not route it.

This overrides the vault's general "capture: file rough, move on / a wrong-but-close home beats the
global inbox" guidance, which governs notes *the user* files by hand. Notes *the agent* writes on
request stay in the inbox until the user says otherwise. Both rules coexist in the vault CLAUDE.md
and the scope of the override has historically been read as ambiguous, which produced a roughly
50/50 split between inbox and direct-to-area filing. It is not ambiguous: **agent-written note on
request → inbox, stop.**

The exception is an explicit destination from the user ("put it in 66"). Then write it there.

## Step 5: Offer connections, then the daily breadcrumb

Connection discovery does not fire on its own, and the user should not have to notice it was
skipped. **Offer it every time**, using the step 1 results plus a fresh search from the finished
note's content.

- Only link notes **confirmed to exist** by an actual search hit. Never emit a `[[link]]` to a note
  you have not verified, and never create side notes on your own initiative. Surface those as
  suggestions ("want me to make a note for X too?") and let the user decide.
- Add links under `## Related` with a few words on *why* each one relates. A bare link list decays.
- Then offer the daily-note breadcrumb:
  ```bash
  npx @techpickles/sb daily append --section "Notes" --content "- [[<note>]] - <one-line why>"
  ```
  Keep it to links unless asked for more. Do not restructure or rewrite the daily note.

For deeper backlink weaving, hand off to the `connect` skill rather than reimplementing it.

## Capturing several sources at once

When the user hands over a batch ("make notes for each of these", "write them up"), dispatch **one
subagent per note** so each reads its source in isolation and cannot cross-contaminate. This is a
pattern the user asks for explicitly; default to it for 3+ sources.

Each subagent: read the primary source, write one note via sb, and report back **path, title,
verified wiki-links used, and anything it could not confirm**. Then do the cross-linking pass
yourself once all notes exist, since connections need the whole set in view.

## Constraints

- **Search first, always.** No note gets written before the user has seen what already exists.
- **Primary sources only.** No note written from a snippet, a memory, or a guess.
- **Never fabricate.** No invented URLs, no unverified `[[links]]`, no filled-in details. Stop and
  report the gap instead.
- **sb owns paths.** No hand-rolled destinations.
- **Inbox by default.** Routing and connecting are offered, not performed.
- **One note, one idea.** If the source carries several distinct ideas, say so and offer to split
  rather than writing one sprawling note.
