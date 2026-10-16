---
name: capture
description: Use when the user asks to read a source and make a note for it, create or find an atomic note, or check whether a note already exists. Triggers on "read <url> and make a note", "make a note for", "create (or find) an atomic note", "do we have notes about X?", "check if we have a note for", "capture this", "put together a note", "distill this", and on a bare URL/PDF/tweet/thread handed over with intent to write it up. Use inside an Obsidian vault or anywhere a vault is configured. Do NOT use for draining an accumulated inbox backlog (that is process-inbox), for extracting insights from the current conversation (that is devlog), or for routing already-captured notes to their homes (that is route).
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
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python3 \"${CLAUDE_PLUGIN_ROOT}\"/hooks/check-sb-before-call.py"
    - matcher: "WebFetch"
      hooks:
        - type: command
          command: "python3 \"${CLAUDE_PLUGIN_ROOT}\"/hooks/webfetch-prefer-lightpanda.py"
---

# Capture

Write a note into the vault from a source the user hands you. One arc, six steps: **open (search,
fetch, ask why) -> read the primary source -> create through sb -> leave it in the inbox -> link
connections -> fold in follow-ups.** "Read this and make a note" means all six; the connect step
won't happen unless this skill runs it.

Note shape: [references/note-format.md](references/note-format.md). sb commands:
[../obsidian/references/sb-cli.md](../obsidian/references/sb-cli.md).

## Step 0: Locate the vault

```bash
npx @techpickles/sb vault info
npx @techpickles/sb config qmd-collection
```

Read the vault's own `CLAUDE.md` if you haven't this session. Its policy (destinations, status
vocabulary, disambiguation) overrides the defaults here.

## Step 1: Open - search, start the fetch, ask why

Do these in order, then end the turn. Nothing is written yet.

1. **Start reading the source in the background** (Bash with `run_in_background`), using the first
   rung of [references/fetch-ladder.md](references/fetch-ladder.md). Step 2 collects the result.
2. **Search the vault while it runs,** through the qmd MCP tools (shelling out to `qmd` hits
   Metal-init failures under the sandbox):

   ```
   mcp__qmd__query
     searches: [{type: 'lex', query: '<one distinctive term>'},
                {type: 'lex', query: '<another term>'},
                {type: 'vec', query: '<what the note would say>'}]
     collection: <from sb config qmd-collection>
     intent: '<why you are searching>'
     rerank: false
   ```

   Each `lex` is one or two terms, because lex ANDs its terms. Also Glob today's inbox captures
   (`*/11 Inbox*/<YYYYMMDD>*.md`), since the qmd index lags same-day notes.
3. **Send one message** with: the hits (path + snippet + why each looks strong or weak; qmd scores
   are only ranks), the question "what made you grab this?", and on a strong match "extend <note>
   or start a new one?".
4. **End the turn.**

Then, keyed to what you observe:

- **The request already states a reason:** skip the why question and carry on.
- **The fetch has failed when you send the message:** say so there, in one line, and ask the same
  questions. The why question and the hits don't wait on the fetch.
- **The fetch finishes before a reply:** write with `**Why I saved this:** TODO`.
- **A strong-match question is open:** wait for the reply, then write.
- **qmd tools aren't loaded yet:** use Grep, say it was keyword-only, and run qmd before writing.
- **A qmd path starts with `second-brain/`:** strip that prefix to get the path on disk.
- **The thing's name is unfamiliar:** let the fetch land before the `vec` query.
- **A search misses, or the user says "that isn't the one":**
  [references/search-recovery.md](references/search-recovery.md).

## Step 2: Read the actual primary source

Never write from search snippets. Read the real thing through the ladder in
[references/fetch-ladder.md](references/fetch-ladder.md): lightpanda first, WebFetch last. If Josh
names a fetch method, use it or say why you can't.

**If you cannot reach the source, or cannot find the thing the user described, stop and say so.**
No URL you did not load, no title you inferred, no details from background knowledge. "I couldn't
find anything matching this" beats a plausible note that is wrong.

## Step 3: Create the note through sb

```bash
npx @techpickles/sb note create --source auto --title "<title>"   # returns JSON with the path
```

Then replace the whole file at that path with this skeleton, filled in. Keep `captured` from sb's
scaffold; everything else in the scaffold goes.

```markdown
---
status: seedling
tags: [topic-tag, another-tag]
created: YYYY-MM-DD
captured: <from sb's scaffold>
source: <the URL or file path you read>
---

# <Title, in the source's own framing>

<What it is, in a sentence or two, with an inline link to the source.>

**Why I saved this:** <the user's reason, in their words - or TODO>

<The content: 3+ parallel items become bullets with a bold lead-in; every named tool, project,
paper, or doc gets its link from the source; every sentence restates the source.>

## Related

- [[<note a search returned>]] - <why it relates>
```

Each slot's rules, with a worked example: [references/note-format.md](references/note-format.md).
**sb owns the path** (inbox, timestamp, slug); hand-rolled `Write` paths once orphaned 46 notes.

## Step 4: Leave it in the inbox for `process-inbox`

The note stays where sb put it: don't ask about routing, don't route it, don't mention that it
needs routing. This overrides the vault's "file rough, move on" guidance, which governs notes the
user files by hand. **Agent-written note on request -> inbox.**

The exception is a destination the user named in the conversation ("put it in 66"). Resolve it as
`route` does: `sb vault structure`, match the phrase to a real destination, then
`sb note move --from "{note-path}" --to "{destination}/"`. Never build the path from the user's
words alone.

## Step 5: Link connections, append the daily breadcrumb

Connection discovery doesn't fire on its own. **Run it every time**, using the Step 1 results plus
a fresh search from the finished note's content. Only the note you just created changes on its own:

- **Confident - add it to the new note, don't ask.** The existing note is the **same subject**
  (same tool/person/project/event, not a shared theme) or is **named in the source**. Add it under
  `## Related` with a few words on *why*, check the target's basename exists first, and say
  `Linked to <note>.` in your summary.
- **Everything else is a proposal,** never an action. If you can't write the "why" without the
  words "theme" or "similar", it's a proposal.

Then append the daily breadcrumb yourself, with no yes/no:

```bash
npx @techpickles/sb daily append --section "Links" --content "- [[<note>]] - <one-line why>"
```

`sb` creates today's daily note from the vault's template when needed and matches the existing
`## Links` heading. Keep it to the link line, and don't pre-check, hand-copy the template,
restructure the daily note, or verify where the line landed. Report it in one line
(`Added breadcrumb to today's daily note.`); if the append fails, say so. A `"created": true`
response means the note was seeded verbatim from the template, so leave any placeholder in it
alone.

### Closing proposals

End the summary with one line per proposal, in exactly this shape:

```
- [high|medium|low] <action in plain words> - <reason> (<path of the existing note>)
```

Actions: `Add a link to this note from <note>`, `Make a note for <thing the source cites>`,
`Add this to <hub or list note>`, `Merge with <note>?`, `Link <note> too?`.

Confidence is how sure you are Josh would say yes, with the reason as proof. Every target is a
note a search found, named by path. Skip the block when there is nothing to propose. For deeper
backlink weaving, hand off to the `connect` skill.

## Step 6: Fold in follow-up research on the note you just wrote

If right after capture the user asks about the thing the note covers ("is there a release date
yet?"), answer and then **update the note** with the answer, rather than leaving it stale in chat.
Say what you added in one line. This stops at a genuinely new note or source.

## Capturing several sources at once

For a batch of 3+ sources, dispatch one subagent per note, then do the cross-linking and closing
proposals yourself. How: [references/batch.md](references/batch.md).

## Constraints

- **Only the new note changes without a yes.** Confident links go inside it and the breadcrumb is
  automatic. Every other note edit and every new side note is a closing proposal, unless the
  user's phrasing already covers the whole batch.
- **Never fabricate.** No invented URLs, no unverified `[[links]]`, no filled-in details.
- **One note, one idea.** If the source carries several distinct ideas, say so and offer to split.
