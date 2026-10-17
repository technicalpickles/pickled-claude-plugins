# Capture follow-up tax: design

Date: 2026-10-16
Scope: `plugins/second-brain/skills/capture/` (this repo), a new skill-scoped hook, the `sb` CLI
(`~/github.com/technicalpickles/sb`, separate repo), and the user's vault
(`~/Vaults/pickled-knowledge`, not in any repo here).

## Intent

When Josh hands over a source to capture, the first note that comes back should be the finished
note. Today it usually isn't. Josh then spends 2-4 more turns asking for things that should
already be there, and the agent spends extra calls correcting its own work inside the turn. This
design removes both kinds of waste.

**Evidence.** On 2026-10-16 we audited all 32 capture sessions since the skill shipped
(2026-08-14), using `cq` over the session transcripts: 10 that invoked the skill on their own, plus
22 typed `/second-brain:capture`. Across the 22 slash-command sessions, Josh sent about 2.5
messages per capture after the first one. That's a rough count that includes plain "yes"es. The
recurring follow-ups:

- **Links he had to ask for.**
  - Related notes: "connect", "were those all existing notes? if so, go ahead to link em".
  - Outbound URLs: "we should be linking to URLs when applicable", "how about doc links for
    mitmweb, the python api, or cli?".
- **Formatting.** "needs to be more scannable".
- **Depth.**
  - "do some more digging, i'm wondering what it looks liek in practice. where are the touch
    points for users".
  - "What is meta harness? I assume it is in the doc but you didn't describe it".
  - "any external links to add and/or capture?".
- **Fetch quality.**
  - "We will need to do an actual content review, not just webfetch".
  - "I'm worried we are usong webfetch which doesn't get full page". This came after he'd
    explicitly asked for a browser and the agent used WebFetch anyway.

In-turn waste that Josh doesn't see but pays for in time:

- **Frontmatter repair.**
  - Agents left `sb`'s scaffold in place: `source: manual` and `repo/branch/commit: none`.
  - They copied `status: filed` / `#tags` from whatever vault note they happened to read.
  - Only the two sessions that explicitly read `note-format.md` got it right.
- **Wasted `--dry-run`.** One per note. In one case it showed a path that differed from the real
  one when the minute rolled over.
- **qmd lex queries miss notes.** Lex queries AND their terms. Verified 2026-10-16:
  `abliterated zzqxnonsense` returns nothing. So a 4-5 word lex query misses notes containing
  only some of the words. This caused duplicate-ish Jev notes and a false "nothing on Jev yet".
- **qmd lags.**
  - The qmd MCP was still connecting at session start in most sessions.
  - The index lags same-day captures. Glean and Falconer were invisible to the Unblocked capture
    an hour later.
- **WebFetch gets facts wrong.** It summarizes, and it invented or garbled facts in 4 sessions.
  It also silently truncates long pages (see task `02c6c391`).
- **Hand-written subagent prompts spread bugs** into every note in a batch: kept the bad
  frontmatter, skipped qmd, guessed `$TMPDIR`. Parallel creates in the same minute share a zettel
  ID.
- **Shell and path slips.**
  - Unquoted `grep --include=*.md` fails under zsh.
  - qmd's `second-brain/` path prefix was treated as an on-disk path.

**Deployment note.** Every audited session ran a stale plugin install: 1.10.0, then 1.13.0. That
means two already-merged fixes never ran:

- #129: drop the daily-append workarounds.
- #141 (2026-09-29): auto-link confident matches into the new note, and fold follow-up answers
  back into it.

Josh updated to 1.17.0 on 2026-10-16. **This design builds on the current SKILL.md, which
includes #141.** Some of the "had to ask for related links" pain may already be gone.

## Goals

1. **The first draft is the finished draft.** It is scannable, links out to what the source names,
   links to related notes the agent verified, records why Josh saved it, and contains only claims
   that trace to fetched content.
2. **Clear lines between automatic, proposed and asked.** Josh knows what will just happen, what
   will come as a proposal, and what never happens without a yes.
3. **The agent reads real content.** Never a summarizer's paraphrase without saying so, and never
   silently.
4. **Fewer wasted calls and self-corrections inside the turn.**

## Non-goals (this round)

- **An extend-existing-note path.** Tracked as task `edf9eff7-fb78-42a6-86ab-0e11b9372bb1`.
- **A lookup-only path** for "do we have notes on X". Tracked as task
  `9d960d03-2383-48f8-9c1c-77037c95fe36`.
- **Trigger recall.** Description tuning, and the `Vaults/rpg` misses. That vault may not be
  configured in `sb`.
- **Why the plugin install went stale for a month.** Real, but separate.
- **Auto-editing other notes.** Revisit later with evidence from proposals Josh accepts.

## Anti-goals

These would make this a failure even if it technically works:

- **More questions.** The "why" question below must never block or add a round trip. If Josh
  doesn't answer, the note still gets written.
- **Silently touching other notes.**
- **Hiding a WebFetch fallback.** A WebFetch fallback that isn't visible in the note is worse than
  today.
- **Padding.** Notes padded with background knowledge or generic "why it matters" sections to look
  thorough.
- **A rigid template applied to every source.** A two-line watchlist note shouldn't grow pricing
  and competitor sections.

## Decisions Josh made

- **Order:** three passes, each shippable on its own:
  1. skill + vault text
  2. WebFetch hook
  3. `sb` CLI
- **Other notes:** only the new note changes automatically. Edits to other notes (backlinks,
  hub/list updates, merges) and new side notes are **proposals**, each with a confidence
  estimate. Josh accepts or declines by hand for now, and we revisit with data later.
- **Fetching:** prefer real-content tools. Hard-deny WebFetch only when a better tool exists and
  hasn't been tried. WebFetch stays as a fallback, and a note built from it carries metadata
  saying so.
- **Why it was saved:** start fetching the source in the background and, meanwhile, ask Josh why
  he's capturing it.
- **Writing skills:** use `writing-tools:writing-for-scannability` for note structure, and the
  `writing-voice` skill, when they're available in the session.
- **In-turn waste counts as scope.** Fix anything that makes the agent take more time or correct
  itself, not just what Josh sees.
- **No `allowed-tools` expansion.** Josh runs captures in auto mode, so fetch commands don't cause
  permission prompts in practice. Leave the skill's `allowed-tools` as is.
- **The build may edit the live vault directly.** It isn't under git, and these edits are small.
  `feedback_link_urls_in_notes.md` gets copied into the skill. The original memory file stays where
  it is, since the sandbox can't write project memory.

## Pass 1: skill and vault text

Changes to `plugins/second-brain/skills/capture/SKILL.md` and `references/note-format.md`, plus
small edits in the vault. Order within the pass is the builder's call.

### Opening: fetch, search and ask in parallel

1. **Start reading the source right away, in the background.** Use a background Bash
   `lightpanda fetch`, or a subagent for multi-page "click around / spelunk" sources.
2. **Run the vault search at the same time** (see Search below).
3. **In the same message, ask one short question:** what made you grab this?
   - Skip it when the request already says why (for example "i'm wondering what it looks like in
     practice"), or when context makes it obvious.
   - Skip it in batch mode.
4. **The search results go in that same message**, so showing what exists and asking cost Josh
   one read, not two turns.
5. **If Josh doesn't answer, don't block.** Write the note anyway with a visible TODO in the "Why I
   saved this" line.

*My call, turn shape:* the opening message (search hits, the why question and, on a strong match,
"extend X or start a new note?") ends the turn while the background fetch keeps running. A
`run_in_background` Bash command re-invokes the agent when it exits. Whichever comes first
triggers the write:

- **Josh's reply comes first:** the agent waits for the fetch, then writes.
- **The fetch finishes first:** the agent writes with the TODO line, unless a strong-match
  question is still open. A strong-match question does block the write, because a duplicate note
  is worse than a wait.

This keeps the current "user sees what exists before anything is written" rule without adding a
round trip. A late "why" answer gets folded in under #141's Step 6.

### Search

1. **Write lex queries as short terms.** Lex ANDs its terms, so use one or two distinctive terms
   per lex sub-query (`jev`, `abliterated`, the product name), and several short lex sub-queries
   rather than one long one. Keep a `vec` sub-query for meaning.
2. **Also list today's inbox captures** (a Glob of today's `YYYYMMDD*` in the inbox folders),
   because qmd's index lags same-day notes.
3. **While qmd is still connecting, fall back to the Grep tool or `rg -g '*.md'`.** Never the
   unquoted `grep --include=*.md`. Say it was keyword-only, then run the qmd pair before writing
   once qmd is up.
4. **Don't claim strength from qmd scores.** They are rank-based (1, .5, .33…). Show path and
   snippet, and say why a hit looks strong or not.
5. **Strip the `second-brain/` collection prefix** from qmd paths to get on-disk paths.
6. **Searching with an unfamiliar name.** It's fine to let the source fetch land first when the
   name is unknown, so the vec query reflects what the thing actually is. The Falconer capture
   searched for "Falconer browser tool" and was wrong.

### Fetch ladder (replaces the Step 2 table)

1. **`lightpanda fetch --dump markdown <url>` via Bash**, when `lightpanda` is on PATH. It needs
   the URL's host in `allowed_domains` under the sandbox. Drop the `mcp__lightpanda__markdown`
   reference: no session ever had that MCP (task `c78a1d05`).
2. **Browser pane** (`get_page_text`, plus `read_page(filter: interactive)` on the nav to list real
   links) for JS-rendered pages and multi-page captures. **Follow real hrefs; never guess subpage
   URLs.** Guessed URLs 404'd twice.
3. **Specialized fetchers:**
   - **Tweets:** `xtweet`.
   - **YouTube:** `yt-dlp --skip-download --write-auto-subs --sub-langs en --sub-format vtt`,
     without `--print`, which implies simulate. Or `yt-infographics` once it has a transcript
     mode.
   - **arXiv:** `arxiv.org/html/<id>` or the PDF via curl, not `/abs/`. Verify cited numbers
     against raw text (task `352b98c7`).
   - **GitHub repos:** `gh api repos/<o>/<r>` and `/readme`.
   - **Hacker News:** the Algolia items API.
   - **Gmail / Drive / Notion / Slack:** their connectors. Local files and uploads: `Read`.
4. **WebFetch, as a last resort.** A note built from it gets frontmatter `fetched-via: webfetch`
   and a one-line body caveat. Long or number-heavy sources must not rely on it alone: it
   truncates silently (task `02c6c391`).
5. **If Josh names a fetch method, use it,** or say plainly why you can't before falling back.

### Creating the note

1. **Drop `--dry-run`.** sb returns the path on create.
2. **Inline the capture frontmatter block in SKILL.md Step 3**, rather than only linking
   note-format.md:
   - `status: seedling`
   - `tags`, with no leading `#`
   - `created`
   - `captured`
   - `source: <url>`
   - optional `via:` for provenance (for example `?ref=producthunt`, "Josh saw it on HN")
   - `fetched-via:` when it fell back to WebFetch
   - drop `repo/branch/commit` when they're `none`

   State outright: **don't copy frontmatter from existing vault notes.** Their `status: filed`,
   `#tags` and `type:` are routed-note or legacy shapes.
3. **The frontmatter fix-up stays in the skill until pass 3 lands.** After that, the skill just
   passes flags.

### What a finished note looks like (`note-format.md` body section)

1. **Scannable.** Bold lead-ins and bullets for anything with parallel parts. Replace the current
   "Prose, not an outline. One to three paragraphs" rule, which contradicts what Josh asked for.
   Use `writing-tools:writing-for-scannability` and `writing-voice` when available. A short clip
   can stay a short paragraph.
2. **Outbound links.** Link every tool, project, paper and doc the source names, using URLs taken
   from the fetched content. Fold in the vault memory `feedback_link_urls_in_notes.md`, which
   currently lives only in the vault's project memory.
3. **"Why I saved this" line.** One line from Josh's answer or the request's phrasing, plus `via:`
   provenance. Never invented.
4. **Define what you name.** If the note mentions a concept from the source (for example
   Meta-Harness), give it one line explaining what it is, or don't mention it.
5. **Shape by kind.** Guidance, not a template:
   - **Product / company page:**
     - what it is, in its own tagline
     - surfaces you actually touch (web, Slack, MCP, CLI, …)
     - integrations
     - deploy and security
     - pricing (check `/pricing`)
     - claims, read skeptically
     - customers
     - competitive set

     This is the shape Josh converged on over four captures on 2026-09-14.
   - **Record (show, game, person):** follow the sibling notes' structure in the target area.
   - **Article / paper:** the argument, the evidence, and what it cites.
6. **Every claim traces to fetched content.**
   - No background-knowledge enrichment ("also founder of Rubrik").
   - No claims about Josh projected from the current repo ("systems Josh operates" about someone
     else's repo).
   - Time-bound pages get "as of <date>" hedges.

### Connections and closing proposals (extends #141's Step 5)

**Automatic, inside the new note:**

- Keep #141's confident links: same subject, or named in the source.
- Verify each target exists, by basename, *before* writing it.

**Proposals at the end of the capture**, each with a confidence (high / medium / low) and a short
reason:

- links back to the new note from existing notes
- side notes for things the source cites that the vault lacks; ending with a list of uncaptured
  references got "please do" twice
- hub or list updates, for example adding a show to the watchlist note
- "this overlaps X, merge?"
- #141's weak links

**Never without a yes:** editing any note other than the new one. That includes reciprocal links;
the Unblocked capture edited the Glean and Falconer notes unasked.

**Use plain words in proposals.** "Add a link to this note from X", not "forward link / backlink".
Every proposed link target is an existing note, and the proposal says so with its path.

### Daily breadcrumb

- Change the skill's `--section "Notes"` to `--section "Links"`. That's what the vault's CLAUDE.md
  rule (4) and the daily template use.

### Batch captures

1. **Subagents invoke the `second-brain:capture` skill** (or are pointed at its SKILL.md) instead
   of getting a hand-written prompt. The hand-written prompts are what spread the frontmatter bug
   and skipped qmd.
2. **Tell subagents to read `$TMPDIR` from the environment,** not guess it.
3. **Subagents report source coverage:** how much of the source they actually retrieved, and any
   suspected truncation (task `bcfce885`).
4. **The orchestrator owns the breadcrumbs, cross-links and closing proposals.** Subagents don't
   touch the daily note.
5. **The orchestrator asks "why" once for the whole batch** and passes the answer to each subagent.

*My call:* SKILL.md gets a short "running as a batch subagent" section. It lists what a subagent
skips: the why question, showing search hits to the user, the breadcrumb, closing proposals and
Step 6. It also lists what a subagent still does: search, fetch ladder, create, note format, and a
coverage report. That's one skill with a clearly marked subset, not a mode flag.

### Vault edits (`~/Vaults/pickled-knowledge`, outside this repo, edited in place)

1. **Daily template:** fix `tags: #daily` (a YAML comment, so the value is lost), and remove the
   literal placeholder `[[202601241234 note-title]]` line so `sb`-created dailies don't inherit it.
2. **CLAUDE.md:** check the daily-linking rule (4) and the other daily-note guidance still agree
   with the skill after this pass. The backdated-link case stays manual until `sb daily append`
   gets `--date` (pass 3).

## Pass 2: WebFetch guardrail hook

A `PreToolUse` hook on `WebFetch`, declared in the capture skill's frontmatter `hooks:` (the same
mechanism as the existing `check-sb-before-call.py`), so it's active only while capture is loaded.

**Behavior:**

- **Allow** when `lightpanda` is not on PATH.
- **Allow** when the session transcript (`transcript_path` from the hook input) shows a lightpanda
  fetch of the same URL, or the same host, that already failed.
- **Otherwise deny,** with a message along the lines of: "Try `lightpanda fetch --dump markdown
  <url>` first (add the host to allowed_domains). If that fails, WebFetch is allowed, and mark the
  note `fetched-via: webfetch`."

**Left to the builder:**

- What "failed" means: exit code, empty output, or a JS-shell page.
- Same URL vs. same host.
- Whether the hook fires inside subagents. Skill-scoped hooks may not apply to them, so the skill
  text has to carry the rule there.
- Tests go in `plugins/second-brain/hooks/tests/`, following the existing pattern.

The browser pane isn't part of the deny logic: a hook can't reliably tell whether it's connected.
The skill text covers when to use it.

*My call, scope:* skill-frontmatter hooks stay registered for the rest of the session once the
skill loads, so this rule will also apply to WebFetch calls outside capture later in that session.
That's acceptable: "try lightpanda first, WebFetch if it fails" is a sensible rule anywhere, and the
deny message spells out the escape hatch. The builder should confirm the actual registration
lifetime and adjust the message if it differs.

## Pass 3: `sb` CLI (`~/github.com/technicalpickles/sb`)

*My call, packaging:* pass 3 gets its own plan and PR in the `sb` repo, including the npm release.
The flag names are that plan's call: a new `--url` flag, or `--source` accepting a URL. Until a
released `sb` version has them, the skill keeps its frontmatter fix-up instructions. A small
follow-up PR here then swaps those for the flags once the release is out.

1. **Capture-shaped frontmatter.** `note create --url <u> --tags a,b`, or `--source <url>` when
   it's a URL, writes:
   - `source: <url>`
   - `status: seedling`
   - `created`
   - `captured`

   It omits `repo/branch/commit` when not in a repo, or when they'd all be `none`. The skill then
   drops its frontmatter fix-up instructions.
2. **Zettel ID collisions.** Parallel creates in the same minute get distinct IDs (bump the
   minute, or detect the existing ID).
3. **Slug.** Collapse repeated hyphens: "Serve / Funnel" became `serve--funnel`.
4. **`daily append` spacing.** Keep the blank line before the next heading. It was eaten in 4
   sessions.
5. **`daily append --date`.** Supports the vault's capture-day linking rule, so backdated links
   stop being hand-edits.
6. **Daily from template.** When `daily append` creates the note from the template, skip or strip
   placeholder-link lines. Also covered by the vault template edit above, belt and braces.

## Verification

- **Existing evals still pass:**
  - `evals/trigger-evals.json`
  - the `no-route-offer` behavior scenario
- **New behavior scenarios**, if the `skill-evals` harness can express them:
  - WebFetch denied when lightpanda exists and hasn't been tried
  - frontmatter shape
  - proposals don't edit other notes
- **Hook unit tests**, matching `hooks/tests/`.
- **Real-use re-audit.** After roughly 10 captures on the new version, re-run the `cq` audit and
  compare follow-ups per capture against the ~2.5 baseline. Check:
  - count of WebFetch-only notes missing `fetched-via`
  - frontmatter correctness
  - zero unasked edits to other notes
  - which proposal types Josh always accepts (input for revisiting automation)

## Folds in existing tasks

Pass 1 should close or update these:

- `02c6c391`: WebFetch truncation
- `352b98c7`: paper / quantitative source row
- `c78a1d05`: lightpanda MCP unavailable
- `bcfce885`: subagent coverage reporting

`15f5f939` (dotfiles `yt-infographics` transcript mode) is already completed. Check whether the
transcript mode exists, and reference it in the fetch ladder.
