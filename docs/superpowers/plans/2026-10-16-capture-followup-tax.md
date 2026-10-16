# Capture Follow-up Tax (passes 1-2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **REQUIRED BACKGROUND:** superpowers:writing-skills. Skill edits follow RED-GREEN-REFACTOR: a case fails against the current skill before the text changes.

**Goal:** Make the capture skill's first draft the finished note, and stop the agent wasting turns.
Four parts:
- rewrite the capture skill's text
- slim it down
- add a hook that sends web fetches through lightpanda before WebFetch
- fix the vault's daily template

**Architecture:**
- **SKILL.md keeps only the core arc,** and gets shorter overall.
- **Heavy reference moves to `references/`:**
  - the fetch ladder
  - batch mode
  - the note contract (in the existing `note-format.md`)
- **Shape problems get templates and output contracts,** not prohibitions.
- **The one discipline problem (WebFetch) is enforced by a `PreToolUse:WebFetch` hook,** declared
  in the skill frontmatter and tested with bats.
- **Behavior is pinned by `claude plugin eval` cases** under `plugins/second-brain/evals/`. Each case is
  written and run red before the text it tests changes.

**Tech Stack:** Markdown skill files, Python 3 (stdlib), bats, `claude plugin eval` (MCP mocks for qmd, a scaffolded fake vault, `regex` / `tool_used` / `llm` graders).

**Spec:** `docs/superpowers/specs/2026-10-16-capture-followup-tax-design.md`. Each task cites its
section. Read it before writing prose.

## Global Constraints

- **Build on the current SKILL.md, which includes #141.** Keep confident-link auto-adding,
  weak-link offers and Step 6 follow-up folding.
- **Keep the Step 0-6 numbering.** Evals and docs reference it.
- **Don't change `allowed-tools`** (spec Decisions).
- **Size:** SKILL.md finishes **under 1,500 words** (it's 2,020 now; check with `wc -w`). Detail
  goes in `references/*.md`, linked with standard markdown links, never `@` imports (repo
  CLAUDE.md "Skill Authoring").
- **Guidance form** (writing-skills "Match the Form to the Failure"):
  - **Output-shape failures** get a template or an ordered contract. This covers frontmatter, note
    body and closing proposals.
  - **No prohibition lists for shape problems.**
  - **No nuance clauses.** Exceptions are conditionals on something observable (e.g. "if the source
    has 3+ parallel items, use bullets").
- **Only the new note changes automatically.** Edits to other notes are proposals with `high` /
  `medium` / `low` plus a reason.
- **Capture frontmatter:**
  - always: `status: seedling`, `tags` (no leading `#`), `created` (`YYYY-MM-DD`), `captured`,
    `source: <url>`
  - optional: `via:`, and `fetched-via: webfetch` when that's how the source was read
  - no `repo/branch/commit` when they're `none`
- **Daily breadcrumb:** `--section "Links"`.
- **Eval cases capture the scaffolded `sources/roc-article.md`** so content is deterministic. Only
  `capture-search-and-fetch` uses a live URL.
- **Commits:** conventional, scope `second-brain`. Every commit ends with
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **A background lightpanda fetch that hasn't finished.** The result reads "Command running in
   background with ID ...". The hook treats that as pending (deny + wait message), not failed.
   Test: `denies with wait message while lightpanda is still running in background`.
2. **Tool-result `content` as a string or as a list of `{"type":"text"}` blocks.** Test:
   `allows after failed lightpanda when result content is a block list`.
3. **`www.` / case host variants** count as the same host. Test:
   `treats www and case variants as the same host`.
4. **Multiple attempts for one host:** the most recent wins. Test:
   `most recent lightpanda attempt for the host wins`.
5. **Unreadable transcript:** allow silently. Test:
   `allows silently when transcript is unreadable`.

---

### Task red-cases: write the eval cases and record the baseline

Spec: "Verification". This is the RED phase for every skill-text task below. It uses
`claude plugin eval`, Claude Code's built-in runner.

**How the runner works**, which shapes these cases:
- Cases live at `plugins/second-brain/evals/<case>/`, as `prompt.md` (frontmatter + prompt) plus
  `graders/*.md`, with an optional `case.yaml` for `context.scaffold_script`.
- Each run gets a throwaway workspace with a fresh HOME.
- **Only MCP tools can be mocked**, at `<case>/mocks/<server>/<tool>.md`. So qmd is mocked; `sb`,
  Read, Write and lightpanda run for real against a scaffolded fake vault.
- **Grader types:**
  - `regex`: `match: contains | not_contains`, with `target: last_message | trace | {source: file, path}`
  - `tool_used`: with `input_match`, and `min: 0, max: 0` to assert a tool was never called
  - `llm`: with `criteria`

**Files:**
- Create: `plugins/second-brain/evals/_shared/scaffold-vault.sh`, a shared scaffold that each
  case's `case.yaml` points at
- Create, one directory per case: `plugins/second-brain/evals/capture-frontmatter/`,
  `capture-note-shape/`, `capture-no-other-note-edits/`, `capture-search-and-fetch/`, and
  `capture-no-route-offer/` (a port of the old `skill-evals` scenario's assertions)
- Create: `plugins/second-brain/evals/README.md`, holding the run command, a case table (name, what
  it pins, baseline result, post-change result) and the spike findings
- Leave the old `skills/capture/evals/` directory alone. Its cases target an internal tool this
  repo can't run.

**Interfaces:**
- Produces: five case names, which later tasks re-run with `$EVAL --case <name>` (see Step 2).

- [ ] **Step 1: Spike: confirm the runner can host a capture.**

Build one throwaway case. Its scaffold makes a vault directory with an `.obsidian/` folder, a
`10-19 System & Capture/11 Inbox & triage/` folder, a `Fleeting/` folder, and one note. Then it
runs `npx -y @techpickles/sb init` (or writes sb's config) so `sb vault info` resolves to that
vault.

Prompt: "run `npx @techpickles/sb vault info`, then create a note titled Spike via sb and write
'hello' into it".

Run that case and read `aggregate-result.json` and the trace. Answer each of these in the README:
- (a) Does `sb vault info` resolve to the scaffold vault?
- (b) How are Bash commands and Write `content` serialized in `trace`? This decides the exact regex
  form the graders use.
- (c) Does a skill-frontmatter `PreToolUse` hook fire? Answer this once task webfetch-guard-hook
  exists, or test it now with a hook that logs to a file.
- (d) Can `{source: file, path: <glob>}` read a note whose timestamped filename isn't known ahead
  of time?

If (a) fails and can't be fixed in the scaffold, stop and report back to Josh. Without sb, there
are no capture evals.

- [ ] **Step 2: Define the run command in the README and use it everywhere below.**

```bash
EVAL="claude plugin eval plugins/second-brain --ablation none --scaffold --trust-plugin \
  --allow-tools Bash Write Edit Read Glob Grep WebFetch --no-publish --runs 3"
```

`--ablation none` is used because the baseline we care about is "the current skill", not "no
plugin".

- [ ] **Step 3: Write the shared scaffold and the qmd mock.**

The scaffold builds on the spike vault and adds three fixture notes:
- `60-69 Software & Engineering/202601010000 astar.md`, with frontmatter `status: filed`,
  `type: reference` and `tags: [#algorithms]`
- `60-69 Software & Engineering/202605050000 roc-algorithm.md`, a short body about Roc
- `sources/roc-article.md`, the "article" the cases capture: a title, a paragraph, four parallel
  features, and three named tools with markdown links
  (`[Rust crate](https://example.com/roc-rs)`, `[Python port](https://example.com/roc-py)`,
  `[benchmarks](https://example.com/roc-bench)`)

The qmd mock at `mocks/qmd/query.md` returns hits for the two vault notes.

Cases capture the local `sources/roc-article.md`, read with `Read`, so the content is
deterministic. Only `capture-search-and-fetch` uses a live URL.

- [ ] **Step 4: Write `capture-frontmatter`.**

Prompt: `Make a note for sources/roc-article.md`.

Graders:
- `regex` on the created note, or on `trace` per spike finding (d), `contains`: `status: seedling`
- `regex` on the same target, `not_contains`: `status: filed`, `repo: none` and `type: reference`
- `regex` on `trace`, `not_contains`: `--dry-run`

- [ ] **Step 5: Write `capture-note-shape`.**

Prompt: `Make a note for sources/roc-article.md, I'm comparing pathfinding libs for my roguelike`.

Graders:
- `regex` `contains`: `Why I saved this` and `https://example.com/roc-rs`
- `llm`, with criteria:
  - the four features appear as bullets
  - the why line mentions the roguelike
  - no fact appears that isn't in the source file

- [ ] **Step 6: Write `capture-no-other-note-edits`.**

Prompt: `Make a note for sources/roc-article.md`.

Graders:
- `tool_used` `Edit`, with `input_match: roc-algorithm`, `min: 0`, `max: 0`
- `tool_used` `Write`, with `input_match: roc-algorithm`, `min: 0`, `max: 0`
- `regex` on `last_message`, `contains` `\[(high|medium|low)\]`, and `not_contains`
  `(?i)backlink|forward link`
- `llm`, with criteria: the final message proposes adding a link to the new note from
  roc-algorithm, with a reason

- [ ] **Step 7: Write `capture-search-and-fetch`.**

Prompt: `Make a note for https://example.com/`. No reason is given.

Graders:
- `regex` on `trace`, `contains`: `lightpanda fetch`
- `tool_used` `mcp__lightpanda__markdown`, with `min: 0`, `max: 0`
- `regex` on `trace`, `not_contains`: `--include=\*\.md`
- `llm`, with criteria:
  - every qmd lex sub-query has at most two terms
  - the agent asks what made the user save it

- [ ] **Step 8: Write `capture-no-route-offer`.**

Prompt: `Make a note for sources/roc-article.md`.

Graders:
- `regex` on `trace`, `not_contains`: `sb note move`
- `llm`, with criterion: no question or reminder about routing, moving or filing the note

- [ ] **Step 9: Run the baseline.**

Run: `$EVAL`
Expected:
- the four new cases each score below 1.0 against the current SKILL.md
- `capture-no-route-offer` scores 1.0

Record each failing grader in the README table, naming the grader.

**If a new case passes at baseline:** it isn't testing a real gap. Tighten it, or drop it and say
why in the README.

- [ ] **Step 10: Commit.**

```bash
git add plugins/second-brain/evals
git commit -m "test(second-brain): capture eval cases with red baseline"
```

### Task slim-and-split: move reference material out of SKILL.md

Spec: none directly. This is the writing-skills size requirement. It's a pure restructure: no
behavior change.

**Files:**
- Create: `plugins/second-brain/skills/capture/references/fetch-ladder.md` (the current Step 2
  source table moves here as its seed)
- Create: `plugins/second-brain/skills/capture/references/batch.md` (the current "Capturing
  several sources at once" body moves here)
- Modify: `plugins/second-brain/skills/capture/SKILL.md`. Step 2 and the batch section shrink to
  2-4 lines each, plus a link. Compress the Step 4 history paragraph ("roughly 50/50 split…")
  down to the rule and one sentence of why.

**Interfaces:**
- Produces:
  - `references/fetch-ladder.md`, which task fetch-ladder fills in
  - `references/batch.md`, which task batch-subagent fills in

- [ ] **Step 1: Move the content and leave links behind.**

- [ ] **Step 2: Verify the size dropped and nothing regressed.**

Run:
```bash
wc -w plugins/second-brain/skills/capture/SKILL.md
```
Expected: the count is below 2,020. Re-run `capture-no-route-offer` (`$EVAL --case capture-no-route-offer`): it still PASSES.

- [ ] **Step 3: Commit.**

```bash
git add plugins/second-brain/skills/capture
git commit -m "refactor(second-brain): move capture reference material into references/"
```

### Task opening-and-search: Step 1 becomes the parallel opening + better search

Spec: "Opening: fetch, search and ask in parallel" (including *My call, turn shape*) and "Search".
GREEN target: `capture-search-and-fetch`, for the lex-term and asks-why expectations.

**Files:**
- Modify: `plugins/second-brain/skills/capture/SKILL.md`: Step 1

**Interfaces:**
- Produces: the heading `## Step 1: Open - search, start the fetch, ask why`.

- [ ] **Step 1: Rewrite Step 1 as an ordered recipe.**
  1. Start the fetch in the background (Bash `run_in_background`).
  2. Search. Each lex sub-query is one or two distinctive terms, because lex ANDs its terms. Also
     run one `vec` query and a Glob of today's `*/11 Inbox*/<YYYYMMDD>*.md`.
  3. Send one message containing the hits (path + snippet + why it looks strong or weak), the why
     question, and an "extend X or new note?" question on a strong match.
  4. End the turn.

  Then the conditionals, each keyed to something observable:
  - **If the request already states a reason:** skip the why question.
  - **If the fetch finishes before a reply:** write with `**Why I saved this:** TODO`.
  - **If a strong-match question is open:** wait for the reply.
  - **If qmd tools aren't loaded yet:** use the Grep tool, say it was keyword-only, and run qmd
    before writing.
  - **If a qmd path starts with `second-brain/`:** strip that prefix for disk paths.

  Keep "When search comes up empty" and "that isn't the one" as they are.

- [ ] **Step 2: Re-run `capture-search-and-fetch` (`$EVAL --case capture-search-and-fetch`).**

Expected: the lex-term and asks-why expectations now PASS. The fetch expectations may still fail
until task fetch-ladder lands.

- [ ] **Step 3: Commit.**

```bash
git add plugins/second-brain/skills/capture/SKILL.md
git commit -m "feat(second-brain): capture opens with parallel fetch, search and why question"
```

### Task fetch-ladder: write the ladder into references/fetch-ladder.md

Spec: "Fetch ladder". This closes tasks `02c6c391`, `352b98c7` and `c78a1d05`. GREEN target:
`capture-search-and-fetch`, for the fetch expectations.

**Files:**
- Modify: `plugins/second-brain/skills/capture/references/fetch-ladder.md`
- Modify: `plugins/second-brain/skills/capture/SKILL.md` Step 2. Keep it to: "read the real
  source via the ladder in [references/fetch-ladder.md](references/fetch-ladder.md)", "if Josh
  names a fetch method, use it or say why you can't", and the existing "cannot reach the source,
  stop and say so" paragraph.

**Interfaces:**
- Produces: the `fetched-via: webfetch` frontmatter key, plus a body caveat line that starts with
  `_Read via WebFetch summary_`.

- [ ] **Step 1: Write the ladder as a numbered list in `fetch-ladder.md`.**
  1. `lightpanda fetch --dump markdown <url>`, with the host in `allowed_domains`.
  2. The browser pane: `get_page_text`, plus `read_page(filter: interactive)` to list real nav
     hrefs. Follow those hrefs.
  3. A source-type table:
     - **tweets:** `xtweet`
     - **YouTube:** `yt-digest --transcript-only <url>`
     - **arXiv:** `arxiv.org/html/<id>` via curl. Re-check cited numbers against the raw text.
     - **GitHub:** `gh api repos/<o>/<r>` plus `/readme`
     - **HN:** Algolia items API
     - **Gmail / Drive / Notion / Slack:** their connectors
     - **local files and uploads:** `Read`
  4. WebFetch. It summarizes and truncates long pages, so set `fetched-via: webfetch` and add the
     caveat line. For long or number-heavy sources, pair it with one of the paths above.

  Add a "Batch / long sources" note: subagents report coverage (task `bcfce885`).

- [ ] **Step 2: Verify.**

Run:
```bash
grep -rc 'mcp__lightpanda' plugins/second-brain/skills/capture/SKILL.md plugins/second-brain/skills/capture/references/
```
Expected: every count is `0`. Re-run `capture-search-and-fetch` (`$EVAL --case capture-search-and-fetch`): it fully PASSES.

- [ ] **Step 3: Commit.**

```bash
git add plugins/second-brain/skills/capture
git commit -m "feat(second-brain): capture reads sources via a fetch ladder, WebFetch last and labeled"
```

### Task frontmatter-template: Step 3 fills a template in one sb call

Spec: "Creating the note". GREEN target: `capture-frontmatter`.

**Files:**
- Modify: `plugins/second-brain/skills/capture/SKILL.md`: Step 3

- [ ] **Step 1: Rewrite Step 3.**
  - A single `npx @techpickles/sb note create --source auto --title "<title>"`.
  - Then "Replace sb's scaffold frontmatter with exactly this block, filled in:", followed by the
    YAML template. The template shows every always-present field from Global Constraints, with
    `via:` and `fetched-via:` as commented-out optional lines.
  - Then one sentence: `captured` comes from sb's scaffold, and everything else in the scaffold
    is dropped.
  - Keep the "sb owns the path" and title paragraphs.

  Don't add a "don't copy from vault notes" line. The template replaces the whole block, so there's
  nothing to copy into.

- [ ] **Step 2: Re-run `capture-frontmatter` (`$EVAL --case capture-frontmatter`).** Expected: PASS (3/3 trials).

- [ ] **Step 3: Commit.**

```bash
git add plugins/second-brain/skills/capture/SKILL.md
git commit -m "feat(second-brain): capture fills a frontmatter template in one sb call"
```

### Task note-contract: note-format.md states the finished note's parts, in order

Spec: "What a finished note looks like". GREEN target: `capture-note-shape`.

**Files:**
- Modify: `plugins/second-brain/skills/capture/references/note-format.md`: the Frontmatter table
  (add `via` and `fetched-via`) and the Body section
- Modify: `plugins/second-brain/skills/capture/SKILL.md`: one line in Step 3, "The body follows the
  contract in [references/note-format.md](references/note-format.md)."

**Interfaces:**
- Produces: the body slot `**Why I saved this:**`, which task opening-and-search writes `TODO` into.

- [ ] **Step 1: Replace the Body rules with an ordered contract.**
  1. `# Title`, in the source's own framing.
  2. An opening line saying what it is, with an inline link to the source.
  3. `**Why I saved this:**` plus Josh's reason. Add `via` provenance when there is one.
  4. The content. If the source has 3+ parallel items, use bold lead-ins and bullets. Link every
     tool, project, paper or doc it names, using URLs from the fetched content. Anything named
     gets a one-line definition. Time-bound facts get "as of [[YYYY-MM-DD]]".
  5. A kind-specific section, chosen by what the source is:
     - **product/company page:** surfaces, integrations, deploy/security, pricing, claims,
       competitors
     - **record:** mirror a sibling note in the target area
     - **article/paper:** argument, evidence, what it cites
  6. `## Related`, last, with verified links only.

  Add one source rule: every sentence restates something in the fetched content.

  Use `writing-tools:writing-for-scannability` and `writing-voice` when available.

  Update the Glide example to follow the contract.

- [ ] **Step 2: Verify.**

Run:
```bash
grep -c 'Prose, not an outline' plugins/second-brain/skills/capture/references/note-format.md
```
Expected: `0`. Re-run `capture-note-shape` (`$EVAL --case capture-note-shape`): it PASSES.

- [ ] **Step 3: Commit.**

```bash
git add plugins/second-brain/skills/capture
git commit -m "feat(second-brain): capture notes follow an ordered contract: why, links, scannable"
```

### Task proposals-contract: Step 5 ends with a fixed closing block

Spec: "Connections and closing proposals" and "Daily breadcrumb". GREEN target:
`capture-no-other-note-edits`.

**Files:**
- Modify: `plugins/second-brain/skills/capture/SKILL.md`: Step 5 and Constraints

- [ ] **Step 1: Rewrite the weak-link part of Step 5 as `### Closing proposals`.**

The closing block is a list. Each item has this form:
```
- [high|medium|low] <action in plain words> - <reason> (<target note path>)
```
- **Actions:**
  - "Add a link to this note from <note>"
  - "Make a note for <cited thing>"
  - "Add this to <hub/list note>"
  - "Merge with <note>?"
  - "Link <note> too?" (this replaces #141's weak-link offer wording)
- **Scope rule (Constraints):** the agent only writes to the note it created. Every other note
  appears in this list instead.
- **Link verification:** keep #141's confident-link rules, and verify each target's basename before
  writing the link.

- [ ] **Step 2: Change the breadcrumb** to `--section "Links"`, and change `## Notes` to `## Links`
  in the surrounding text.

- [ ] **Step 3: Re-run `capture-no-other-note-edits` (`$EVAL --case capture-no-other-note-edits`) and `capture-no-route-offer`.** Expected: both PASS.

- [ ] **Step 4: Commit.**

```bash
git add plugins/second-brain/skills/capture/SKILL.md
git commit -m "feat(second-brain): capture closes with confidence-labeled proposals, edits only its own note"
```

### Task batch-subagent: fill references/batch.md

Spec: "Batch captures". This closes task `bcfce885`.

**Files:**
- Modify: `plugins/second-brain/skills/capture/references/batch.md`

- [ ] **Step 1: Write two sections.**
  - **Orchestrator:**
    - ask "why" once and pass it down
    - each subagent prompt says "invoke the `second-brain:capture` skill, follow Running as a batch
      subagent, `$TMPDIR` is `<value of echo $TMPDIR>`"
    - after all notes exist, do the breadcrumbs, cross-links and closing proposals
  - **Running as a batch subagent,** as a two-column table:
    - **Does:** search, fetch ladder, create, note contract
    - **Skips:** the why question, showing hits, the breadcrumb, closing proposals, Step 6
    - **Report back:** path, title, verified links, unconfirmed items, and coverage (rough % of the
      source retrieved, plus suspected truncation)

- [ ] **Step 2: Verify.**

Run:
```bash
grep -n -e 'Running as a batch subagent' -e 'coverage' -e 'TMPDIR' plugins/second-brain/skills/capture/references/batch.md
```
Expected: at least one line for each pattern.

- [ ] **Step 3: Commit.**

```bash
git add plugins/second-brain/skills/capture/references/batch.md
git commit -m "feat(second-brain): batch capture subagents run the skill and report coverage"
```

### Task webfetch-guard-hook: PreToolUse hook that prefers lightpanda

Spec: "Pass 2: WebFetch guardrail hook". The open choices are decided here:
- **failed** = `is_error: true`, or under 200 characters of text after stripping
- **pending** = the text contains `running in background`
- **host matching** is lowercased, with a leading `www.` stripped

**Files:**
- Create: `plugins/second-brain/hooks/webfetch-prefer-lightpanda.py` (executable)
- Create: `plugins/second-brain/hooks/tests/webfetch-prefer-lightpanda.bats`
- Modify: `plugins/second-brain/skills/capture/SKILL.md`. Add a frontmatter `hooks.PreToolUse`
  entry with `matcher: "WebFetch"`, running
  `python3 "${CLAUDE_PLUGIN_ROOT}"/hooks/webfetch-prefer-lightpanda.py`.

**Interfaces:**
- Consumes: stdin JSON `tool_input.url` and `transcript_path`. The transcript is JSONL: assistant
  `message.content[]` `{type:"tool_use", id, name:"Bash", input:{command}}`, and user
  `{type:"tool_result", tool_use_id, is_error?, content}`, where `content` is a string or a list of
  `{type:"text", text}`.
- Produces:
  - **deny:** stdout `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":<msg>}}`
  - **allow:** exit 0 with no output

**Decision order:**
1. Malformed stdin or an unreadable transcript → allow.
2. `shutil.which("lightpanda")` is None → allow.
3. Otherwise, look at the most recent Bash `tool_use` whose command contains `lightpanda` and a URL
   with the same host:
   - none → deny (try-first)
   - pending → deny (wait)
   - failed → allow
   - otherwise → deny (try-first)

**Exact copy** (substitute the real URL for `<url>`):
- **Try-first:** `Try lightpanda before WebFetch: lightpanda fetch --dump markdown <url> (add the host to allowed_domains). If that fails, WebFetch is allowed - mark the note fetched-via: webfetch.`
- **Wait:** `A lightpanda fetch for this host is still running in the background. Wait for it to finish instead of falling back to WebFetch.`

- [ ] **Step 1: Write the failing bats tests.**

Follow `tests/check-sb-before-call.bats`.
- `setup` creates `FAKE_BIN`, with a stub `lightpanda` (`#!/bin/sh`, `exit 0`), and captures
  `PYTHON="$(command -v python3)"`.
- Run the hook as `PATH="$FAKE_BIN:/usr/bin:/bin" "$PYTHON" "$HOOK"`.
- Add a helper `write_attempt <url> <is_error> <content-json>` that appends a matching
  tool_use/tool_result pair.

Tests:
- `allows silently when lightpanda is not on PATH`: status 0, empty output.
- `denies when lightpanda exists and was never tried`: output contains `"permissionDecision": "deny"` and `lightpanda fetch --dump markdown https://glean.com/`.
- `allows after failed lightpanda for the same host`: empty output.
- `allows after lightpanda returned near-empty output`: content `"<html></html>"`. Empty output.
- `allows after failed lightpanda when result content is a block list`: empty output.
- `denies when the failed attempt was for a different host`: output contains `deny`.
- `denies after a successful lightpanda fetch`: 500 characters of content. Output contains `deny`.
- `denies with wait message while lightpanda is still running in background`: output contains `still running in the background`.
- `treats www and case variants as the same host`: failed on `https://glean.com/x`, WebFetch on `https://www.Glean.com/y`. Empty output.
- `most recent lightpanda attempt for the host wins`: failed, then 500 characters of content. Output contains `deny`.
- `allows silently when transcript is unreadable`: empty output.
- `allows silently on malformed stdin`: empty output.

- [ ] **Step 2: Run the tests and confirm they fail.**

Run: `bats plugins/second-brain/hooks/tests/webfetch-prefer-lightpanda.bats`
Expected: all fail (the hook doesn't exist yet).

- [ ] **Step 3: Implement the hook.**

Use stdlib only. Write the docstring in the style of `check-sb-before-call.py`, and note there that
the hook stays registered for the session once capture loads. Read the transcript line by line and
skip lines that don't parse. Find URLs with `re.findall(r'https?://[^\s\'"]+', command)`.

- [ ] **Step 4: Run all hook tests.**

Run: `bats plugins/second-brain/hooks/tests/`
Expected: all pass.

- [ ] **Step 5: Register the hook and check the frontmatter parses.**

Run:
```bash
uv run --with pyyaml python -c "import yaml; t=open('plugins/second-brain/skills/capture/SKILL.md').read().split('---')[1]; print([h['matcher'] for h in yaml.safe_load(t)['hooks']['PreToolUse']])"
```
Expected: `['Bash', 'WebFetch']`

- [ ] **Step 6: Commit.**

```bash
git add plugins/second-brain/hooks plugins/second-brain/skills/capture/SKILL.md
git commit -m "feat(second-brain): capture hook prefers lightpanda over WebFetch"
```

### Task description-triggers: description says when, not how

Writing-skills SDO says a description that summarizes the workflow lets agents follow the summary
and skip the body.

**Files:**
- Modify: `plugins/second-brain/skills/capture/SKILL.md`: the frontmatter `description`

- [ ] **Step 1: Record baseline recall and precision.** Run the existing trigger eval as described
  in `evals/README.md` ("Trigger evals for `capture`"). Save the numbers.

- [ ] **Step 2: Remove the workflow summary from the description.** Delete the sentence that
  starts "Covers the whole loop as one arc". Keep every trigger phrase and the "Do NOT use for"
  routing.

- [ ] **Step 3: Re-run the trigger eval.**

Expected: recall and precision within ±1 query of the baseline. If recall drops, restore the
sentence and record the result in `evals/README.md`. The repo CLAUDE.md says recall here may be
pointer-driven ("Description Tuning Has a Structural Ceiling").

- [ ] **Step 4: Commit.**

```bash
git add plugins/second-brain/skills/capture
git commit -m "fix(second-brain): capture description lists triggers only"
```

### Task green-refactor: full case pass and loophole closing

- [ ] **Step 1: Run the full suite (`$EVAL`).**

Expected: all PASS. Fill in the README table's post-change column.

- [ ] **Step 2: Handle any case that is flaky** (passes in some trials, fails in others). Read
  the failing transcripts. Name the rationalization or misread, and tighten the form: make a recipe
  step or template slot more specific rather than adding a prohibition. Re-run until 3/3. Commit as
  `fix(second-brain): ...`.

- [ ] **Step 3: Size check.**

Run: `wc -w plugins/second-brain/skills/capture/SKILL.md`
Expected: under 1,500.

### Task vault-edits: fix the daily template and check CLAUDE.md

Spec: "Vault edits". These are outside the repo: edit in place, no commit.

**Files:**
- Modify: `~/Vaults/pickled-knowledge/Templates/daily.md`
- Check, and modify only if it contradicts the skill: `~/Vaults/pickled-knowledge/CLAUDE.md`. Look
  at the "Daily Note Pattern" example (around lines 244-270) and rule (4) (around line 90).

- [ ] **Step 1: Fix the template.** In `Templates/daily.md`, change `tags: #daily` to
  `tags: [daily]`, and delete the placeholder `[[202601241234 ...]]` line under `## Links`.

- [ ] **Step 2: Apply the same fixes to the CLAUDE.md example block.** Leave rule (4) alone if it
  already agrees with the skill (`## Links`, backdated links by hand until `sb daily append --date`
  exists).

- [ ] **Step 3: Verify.**

Run: `grep -n -e 'tags:' -e '202601241234' ~/Vaults/pickled-knowledge/Templates/daily.md`
Expected: `tags: [daily]`, and no placeholder line.

### Task release: version bump and task cleanup

**Files:**
- Modify: `.claude-plugin/marketplace.json` and `README.md`, both via the script

- [ ] **Step 1: Bump the version.** Run `./scripts/bump-version.sh --auto`. Expected: `second-brain`
  gets a minor bump.

- [ ] **Step 2: Commit the bump.**

```bash
git add .claude-plugin/marketplace.json README.md
git commit -m "chore(second-brain): bump version to <X.Y.Z>"
```

- [ ] **Step 3: Close the folded-in tasks.**

Run:
```bash
for u in 02c6c391 352b98c7 c78a1d05 bcfce885; do
  task "$u" annotate "Addressed on branch capture-followup-tax (capture follow-up-tax design, 2026-10-16)"
  task "$u" done
done
```
Expected: 4 tasks completed.
