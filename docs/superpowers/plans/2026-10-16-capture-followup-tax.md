# Capture Follow-up Tax (passes 1-2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the capture skill's first draft the finished note, and stop the agent wasting turns.
Two parts: rewrite the capture skill's text (and fix the vault template), and add a hook that
pushes web fetches through lightpanda before WebFetch.

**Architecture:**

- **Skill text:** `plugins/second-brain/skills/capture/SKILL.md` and `references/note-format.md`.
  These are the model's instructions, so that's where most of the work is.
- **The hook:** one new Python file, `PreToolUse:WebFetch`. It's declared in the skill's
  frontmatter, next to the existing `check-sb-before-call.py`, and tested with bats like that hook.
- **Vault edits:** made in place, in `~/Vaults/pickled-knowledge` (not a git repo).

**Tech Stack:** Markdown skill files, Python 3 (stdlib only), bats.

**Spec:** `docs/superpowers/specs/2026-10-16-capture-followup-tax-design.md`. Every task below cites
the spec section it implements. Read that section before writing the prose.

## Global Constraints

- **Build on the current SKILL.md, which already includes #141.** Keep confident-link
  auto-adding, weak-link offers and Step 6's follow-up folding.
- **Keep the existing Step 0-6 numbering.** New material goes inside existing steps or under new
  `###` subsections. `evals/` and other docs reference step numbers.
- **Don't change `allowed-tools`** (spec: Decisions, no expansion).
- **Only the new note changes automatically.** Edits to any other note are proposals that need a
  yes.
- **Proposals carry `high` / `medium` / `low` plus a short reason.** Not percentages.
- **Frontmatter for a capture:** `status: seedling`, `tags` (no leading `#`), `created`
  (`YYYY-MM-DD`), `captured`, and `source: <url>`. Optionally `via:`, and `fetched-via: webfetch`
  when that's how it was read. Drop `repo/branch/commit` when they're `none`.
- **Daily breadcrumb section:** `--section "Links"`.
- **Commits:** conventional, scope `second-brain` (e.g. `feat(second-brain): ...`), ending with
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **A background lightpanda fetch that hasn't finished yet.** The tool result is just "Command
   running in background with ID ...", not page content. The hook must treat that as *pending*
   (deny, with a message to wait for it), not as *failed*. Test:
   `denies with wait message while lightpanda is still running in background`.
2. **Tool-result `content` comes in two shapes:** a plain string, or a list of
   `{"type":"text","text":...}` blocks. Both must parse. Test:
   `allows after failed lightpanda when result content is a block list`.
3. **Hosts that differ only by `www.` or case** (`www.Glean.com` vs `glean.com`) are the same host.
   Test: `treats www and case variants as the same host`.
4. **Several attempts for one host.** The most recent attempt decides. A failure followed by a
   success means deny. Test: `most recent lightpanda attempt for the host wins`.
5. **An unreadable or missing transcript fails open** (allow silently). The hook must never block
   because it couldn't read its own input. Test: `allows silently when transcript is unreadable`.

---

### Task opening-and-search: Step 1 becomes the parallel opening + better search

Spec: "Opening: fetch, search and ask in parallel" (including *My call, turn shape*) and "Search".

**Files:**
- Modify: `plugins/second-brain/skills/capture/SKILL.md`: "Step 1" through the end of "When the
  user says 'that isn't the one'"

**Interfaces:**
- Produces: the Step 1 heading `## Step 1: Open - search, start the fetch, ask why`. Later tasks
  and the batch section refer to "the Step 1 why question" and "the Step 1 strong-match question".

- [ ] **Step 1: Rewrite Step 1.**
  - **New opening subsection (`### Kick off in parallel`):**
    - Start the source fetch in the background, with Bash `run_in_background` (lightpanda), or a
      subagent for multi-page sources.
    - Run the search.
    - Send one message with: the search hits, the why question (skipped when the request already
      says why, when context makes it obvious, or in batch mode), and an "extend X or new note?"
      question on a strong match.
    - End the turn.
  - **What triggers the write:** whichever comes first, Josh's reply or the fetch finishing. If the
    fetch finishes first, write with `Why I saved this: TODO`. A still-open strong-match question
    blocks the write. A late why answer gets folded in via Step 6.
  - **Search subsection, replacing the current one:**
    - Short lex terms, with a one-line reason: lex ANDs its terms. Several lex sub-queries plus one
      `vec`.
    - Glob today's inbox captures (`*/11 Inbox*/<YYYYMMDD>*.md`), because qmd lags.
    - While qmd is connecting, use the Grep tool or `rg -l -g '*.md' <term>`. Never use unquoted
      `grep --include=*.md`. Say the search was keyword-only.
    - qmd scores are rank-based: show path + snippet and say why a hit looks strong.
    - Strip the `second-brain/` prefix to get disk paths.
    - For an unfamiliar name, the fetch may land before the vec query is written.
  - **Keep as-is:** "When search comes up empty" and "that isn't the one".

- [ ] **Step 2: Verify the old guidance is gone and the new guidance is present.**

Run:
```bash
f=plugins/second-brain/skills/capture/SKILL.md
grep -c 'path + score + snippet' $f
grep -n -e 'run_in_background' -e 'AND' -e 'rg -l' -e 'second-brain/' -e 'Why I saved this' $f
```
Expected: the first count is `0`. The second prints at least one line for each pattern.

- [ ] **Step 3: Commit.**

```bash
git add plugins/second-brain/skills/capture/SKILL.md
git commit -m "feat(second-brain): capture opens with parallel fetch, search and why question"
```

### Task fetch-ladder: Step 2 becomes the fetch ladder

Spec: "Fetch ladder (replaces the Step 2 table)". This closes the gaps behind tasks `02c6c391`,
`352b98c7` and `c78a1d05`.

**Files:**
- Modify: `plugins/second-brain/skills/capture/SKILL.md`: the "Step 2" table and the text around it

**Interfaces:**
- Produces: the frontmatter key `fetched-via: webfetch` and the body caveat. Both are referenced by
  task note-shape and the hook's deny message (task webfetch-guard-hook).

- [ ] **Step 1: Replace the Step 2 table with an ordered ladder.**
  - **The ladder:**
    1. `lightpanda fetch --dump markdown <url>`, with the host in `allowed_domains`.
    2. The browser pane: `get_page_text`, and `read_page(filter: interactive)` to list real nav
       links. Follow hrefs and never guess subpage URLs.
    3. Specialized fetchers:
       - **tweets:** `xtweet`
       - **YouTube:** `yt-digest --transcript-only <url>`
       - **arXiv:** `arxiv.org/html/<id>` via curl (not `/abs/`), plus verify cited numbers
         against the raw text
       - **GitHub:** `gh api repos/<o>/<r>` plus `/readme`
       - **HN:** the Algolia items API
       - **Gmail / Drive / Notion / Slack:** their connectors
       - **local files and uploads:** `Read`
    4. WebFetch last. It summarizes and silently truncates long pages, so it's never the sole
       source for numbers. Set `fetched-via: webfetch` and add a one-line body caveat.
  - **Add:** "If Josh names a fetch method, use it or say why you can't."
  - **Keep** the "If you cannot reach the source… stop and say so" paragraph.
  - **Remove** every `mcp__lightpanda__markdown` reference.

- [ ] **Step 2: Verify.**

Run:
```bash
f=plugins/second-brain/skills/capture/SKILL.md
grep -c 'mcp__lightpanda' $f
grep -n -e 'lightpanda fetch --dump markdown' -e 'yt-digest --transcript-only' -e 'arxiv.org/html' -e 'fetched-via: webfetch' -e 'names a fetch method' $f
```
Expected: `0`, then at least one line for each of the 5 patterns.

- [ ] **Step 3: Commit.**

```bash
git add plugins/second-brain/skills/capture/SKILL.md
git commit -m "feat(second-brain): capture reads sources via a fetch ladder, WebFetch last and labeled"
```

### Task create-and-frontmatter: Step 3 drops the dry-run and inlines frontmatter

Spec: "Creating the note".

**Files:**
- Modify: `plugins/second-brain/skills/capture/SKILL.md`: "Step 3"

**Interfaces:**
- Consumes: `fetched-via` from task fetch-ladder.

- [ ] **Step 1: Rewrite Step 3.**
  - **Use a single** `npx @techpickles/sb note create --source auto --title "<title>"`. No
    `--dry-run` line.
  - **Inline the capture frontmatter block** (the Global Constraints shape, as a YAML example).
  - **Say what to do with sb's scaffold:** replace `source: manual` with the URL, drop
    `repo/branch/commit` when they're `none`, add `status/tags/created`.
  - **Add the bold rule:** don't copy frontmatter from existing vault notes. Their `status: filed`,
    `#tags` and `type:` are routed-note or legacy shapes.
  - **Keep** the "Do not hand-roll the destination path" and title paragraphs.

- [ ] **Step 2: Verify.**

Run:
```bash
f=plugins/second-brain/skills/capture/SKILL.md
grep -c -- '--dry-run' $f
grep -n -i -e 'status: seedling' -e "don't copy frontmatter" -e 'source: manual' $f
```
Expected: `0`, then at least one line for each pattern.

- [ ] **Step 3: Commit.**

```bash
git add plugins/second-brain/skills/capture/SKILL.md
git commit -m "feat(second-brain): capture creates in one sb call with inline frontmatter"
```

### Task note-shape: note-format.md describes the finished note

Spec: "What a finished note looks like".

**Files:**
- Modify: `plugins/second-brain/skills/capture/references/note-format.md`: the Frontmatter table
  and the Body section

**Interfaces:**
- Produces: a body line labeled exactly `**Why I saved this:**`. Task opening-and-search writes
  `TODO` there.

- [ ] **Step 1: Update the Frontmatter table.** Add rows for `via` (provenance, e.g. a `?ref=`
  referrer or where Josh saw it) and `fetched-via` (set to `webfetch` only when WebFetch was the
  source).

- [ ] **Step 2: Rewrite the Body rules.**
  - **Replace "Prose, not an outline. One to three paragraphs"** with: scannable, meaning bold
    lead-ins and bullets for parallel parts, while a short clip can stay a short paragraph. Use
    `writing-tools:writing-for-scannability` and `writing-voice` when they're available.
  - **Outbound links** to every tool, project, paper or doc the source names, with URLs taken
    from the fetched content.
  - **`**Why I saved this:**` line**, placed after the opening paragraph.
  - **Define what you name**, in one line, or don't mention it.
  - **Shape by kind:** product page, record, article/paper. Use the spec's lists, written as
    guidance, not a template.
  - **Every claim traces to fetched content.** No background enrichment, no claims about Josh
    taken from cwd, and "as of <date>" for time-bound pages.
  - **Update the example body** to show bullets, an outbound link and the why line.
  - **Keep** `## Related` last, plus the verified-links rules.

- [ ] **Step 3: Verify.**

Run:
```bash
f=plugins/second-brain/skills/capture/references/note-format.md
grep -c 'Prose, not an outline' $f
grep -n -e 'Why I saved this' -e 'fetched-via' -e 'via' -e 'writing-for-scannability' -e 'pricing' -e 'as of' $f
```
Expected: `0`, then at least one line for each pattern.

- [ ] **Step 4: Commit.**

```bash
git add plugins/second-brain/skills/capture/references/note-format.md
git commit -m "feat(second-brain): capture notes are scannable, link out, and record why"
```

### Task proposals: Step 5 splits automatic links from proposals

Spec: "Connections and closing proposals" and "Daily breadcrumb". The Constraints section must
stay consistent with these changes.

**Files:**
- Modify: `plugins/second-brain/skills/capture/SKILL.md`: "Step 5" and "Constraints"

- [ ] **Step 1: Rewrite the weak-link part of Step 5 as `### Closing proposals`.**
  - **Proposal kinds:** links back to the new note from existing notes, side notes for cited
    things the vault lacks, hub/list updates, "this overlaps X, merge?", and #141's weak links.
  - **Each proposal** gets `high`/`medium`/`low` and a reason, uses plain words ("add a link to
    this note from X", never "forward link"/"backlink"), and shows the target's path.
  - **Keep #141's confident-link rules,** adding: verify each target's basename exists *before*
    writing the link.

- [ ] **Step 2: Fix the breadcrumb section name and update Constraints.**
  - **Breadcrumb command:** change it to `--section "Links"`, and change the `## Notes` mention to
    `## Links`.
  - **Constraints:** add "Never edit a note other than the one just written without a yes. That
    includes reciprocal links."

- [ ] **Step 3: Verify.**

Run:
```bash
f=plugins/second-brain/skills/capture/SKILL.md
grep -c -e '--section "Notes"' -e 'forward link' $f
grep -n -e '--section "Links"' -e 'high' -e 'Closing proposals' -e 'other than the one just written' $f
```
Expected: `0`, then at least one line for each pattern.

- [ ] **Step 4: Commit.**

```bash
git add plugins/second-brain/skills/capture/SKILL.md
git commit -m "feat(second-brain): capture proposes cross-note edits with confidence, never applies them"
```

### Task batch-subagent: batch section and the subagent subset

Spec: "Batch captures" (including its *My call*). This closes the gap behind task `bcfce885`.

**Files:**
- Modify: `plugins/second-brain/skills/capture/SKILL.md`: "Capturing several sources at once"

- [ ] **Step 1: Rewrite the batch section.**
  - **The orchestrator:** asks the why question once and passes the answer down, then owns the
    breadcrumbs, cross-links and closing proposals.
  - **Each subagent's prompt:** tells it to invoke the `second-brain:capture` skill and follow
    `### Running as a batch subagent`, with no hand-written capture instructions. It also tells it
    to read `$TMPDIR` from the environment rather than guess it.
  - **New `### Running as a batch subagent` subsection:**
    - **Skip:** the why question, showing hits to the user, the breadcrumb, closing proposals and
      Step 6.
    - **Do:** search, fetch ladder, create, note format, and report back path, title, verified
      links, unconfirmed items, and **coverage** (roughly how much of the source was actually
      retrieved, plus any suspected truncation).

- [ ] **Step 2: Verify.**

Run:
```bash
grep -n -e 'Running as a batch subagent' -e 'coverage' -e 'TMPDIR' -e 'second-brain:capture' plugins/second-brain/skills/capture/SKILL.md
```
Expected: at least one line for each pattern.

- [ ] **Step 3: Commit.**

```bash
git add plugins/second-brain/skills/capture/SKILL.md
git commit -m "feat(second-brain): batch capture subagents run the skill and report coverage"
```

### Task webfetch-guard-hook: PreToolUse hook that prefers lightpanda

Spec: "Pass 2: WebFetch guardrail hook". Its open choices are decided here:

- **"Failed"** means the tool result has `is_error: true`, or its text is under 200 characters
  after stripping.
- **"Pending"** means the text contains `running in background`.
- **Matching is by host:** lowercased, with a leading `www.` stripped.

**Files:**
- Create: `plugins/second-brain/hooks/webfetch-prefer-lightpanda.py`
- Create: `plugins/second-brain/hooks/tests/webfetch-prefer-lightpanda.bats`
- Modify: `plugins/second-brain/skills/capture/SKILL.md`: frontmatter `hooks.PreToolUse`, adding a
  `matcher: "WebFetch"` entry that runs `python3 "${CLAUDE_PLUGIN_ROOT}"/hooks/webfetch-prefer-lightpanda.py`

**Interfaces:**
- Consumes: hook stdin JSON, using `tool_input.url` and `transcript_path`. The transcript is JSONL:
  - assistant lines carry `message.content[]` items `{type:"tool_use", id, name:"Bash", input:{command}}`
  - user lines carry `{type:"tool_result", tool_use_id, is_error?, content}`, where `content` is a
    string or a list of `{type:"text", text}`
- Produces, on stdout:
  - **deny:** `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":<msg>}}`
  - **allow:** exit 0, no output

**Decision order:**
1. Malformed stdin or an unreadable transcript: allow.
2. `shutil.which("lightpanda")` is None: allow.
3. Find the most recent Bash `tool_use` whose command contains `lightpanda` and whose URL host
   matches.
   - **None found:** deny with the try-first message.
   - **Pending:** deny with the wait message.
   - **Failed:** allow.
   - **Succeeded:** deny with the try-first message.

**Exact deny copy:**
- **Try-first:** `Try lightpanda before WebFetch: lightpanda fetch --dump markdown <url> (add the host to allowed_domains). If that fails, WebFetch is allowed - mark the note fetched-via: webfetch.`
- **Wait:** `A lightpanda fetch for this host is still running in the background. Wait for it to finish instead of falling back to WebFetch.`

In both messages, substitute the real URL for `<url>`.

- [ ] **Step 1: Write the failing bats tests.**

Follow `tests/check-sb-before-call.bats`:
- `setup` creates `FAKE_BIN`, with a stub `lightpanda` (`#!/bin/sh` + `exit 0`), and a temp
  transcript path.
- Run the hook as `PATH="$FAKE_BIN:/usr/bin:/bin" "$PYTHON" "$HOOK"`, where
  `PYTHON="$(command -v python3)"` is captured in `setup`, so removing lightpanda from PATH doesn't
  lose python.
- A helper `write_attempt <url> <is_error> <content-json>` appends one matching tool_use/tool_result
  line pair to the transcript.

Tests:
- `allows silently when lightpanda is not on PATH`: PATH has no stub. Status 0, empty output.
- `denies when lightpanda exists and was never tried`: output contains `"permissionDecision": "deny"` and `lightpanda fetch --dump markdown https://glean.com/`.
- `allows after failed lightpanda for the same host`: is_error true. Status 0, empty output.
- `allows after lightpanda returned near-empty output`: content `"<html></html>"`. Empty output.
- `allows after failed lightpanda when result content is a block list`: content
  `[{"type":"text","text":"Error: navigation failed"}]` with is_error true. Empty output.
- `denies when the failed attempt was for a different host`: attempt on `https://falconer.com/`,
  WebFetch on `https://glean.com/`. Output contains `deny`.
- `denies after a successful lightpanda fetch`: content is 500 characters. Output contains `deny`.
- `denies with wait message while lightpanda is still running in background`: content
  `"Command running in background with ID: abc123"`. Output contains `still running in the background`.
- `treats www and case variants as the same host`: a failed attempt on `https://glean.com/x`,
  WebFetch on `https://www.Glean.com/y`. Empty output.
- `most recent lightpanda attempt for the host wins`: a failed attempt, then a successful one
  (500 characters). Output contains `deny`.
- `allows silently when transcript is unreadable`: `transcript_path` points at a nonexistent file.
  Empty output.
- `allows silently on malformed stdin`: stdin `not json`. Empty output.

- [ ] **Step 2: Run the tests to verify they fail.**

Run: `bats plugins/second-brain/hooks/tests/webfetch-prefer-lightpanda.bats`
Expected: every test fails (the hook file doesn't exist).

- [ ] **Step 3: Implement the hook.**

Write `plugins/second-brain/hooks/webfetch-prefer-lightpanda.py`. Use stdlib only (`json`, `sys`,
`shutil`, `urllib.parse`). The module docstring follows `check-sb-before-call.py`'s style and says
the hook is skill-scoped and stays registered for the session once capture loads. Read the
transcript line by line and skip lines that fail to parse. Extract URLs from a Bash command with
`re.findall(r'https?://[^\s\'"]+', command)`. Make it executable (`chmod +x`).

- [ ] **Step 4: Run the tests to verify they pass.**

Run: `bats plugins/second-brain/hooks/tests/`
Expected: all tests pass, the existing ones included.

- [ ] **Step 5: Register the hook in the SKILL.md frontmatter, and verify the YAML parses.**

Run:
```bash
uv run --with pyyaml python -c "import yaml,sys; t=open('plugins/second-brain/skills/capture/SKILL.md').read().split('---')[1]; print([h['matcher'] for h in yaml.safe_load(t)['hooks']['PreToolUse']])"
```
Expected: `['Bash', 'WebFetch']`

- [ ] **Step 6: Commit.**

```bash
git add plugins/second-brain/hooks/webfetch-prefer-lightpanda.py plugins/second-brain/hooks/tests/webfetch-prefer-lightpanda.bats plugins/second-brain/skills/capture/SKILL.md
git commit -m "feat(second-brain): capture hook prefers lightpanda over WebFetch"
```

### Task vault-edits: fix the daily template and check CLAUDE.md

Spec: "Vault edits". These files sit outside the repo: edit them in place, with no commit.

**Files:**
- Modify: `~/Vaults/pickled-knowledge/Templates/daily.md`
- Check, and modify only if it contradicts the skill: `~/Vaults/pickled-knowledge/CLAUDE.md`, the
  "Daily Note Pattern" section (around lines 244-270) and rule (4) (around line 90)

- [ ] **Step 1: Fix the template.**
  - Change `tags: #daily` to `tags: [daily]`.
  - Delete the placeholder `[[202601241234 ...]]` line under `## Links`, keeping the heading.

- [ ] **Step 2: Fix the CLAUDE.md example.** In the "Typical structure" example block, apply the
  same two fixes. Confirm that rule (4) still matches the skill: `## Links` section, and
  backdated links done by hand until `sb daily append --date` exists. Leave rule (4) alone if it
  agrees.

- [ ] **Step 3: Verify.**

Run:
```bash
grep -n -e 'tags:' -e '202601241234' ~/Vaults/pickled-knowledge/Templates/daily.md
```
Expected: `tags: [daily]`, and no `202601241234` line.

### Task release: version bump and task cleanup

**Files:**
- Modify: `.claude-plugin/marketplace.json`, and `README.md` if it's regenerated (both via the
  script)

- [ ] **Step 1: Run the existing tests.**

Run: `bats plugins/second-brain/hooks/tests/`
Expected: all pass.

- [ ] **Step 2: Bump the version.**

Run: `./scripts/bump-version.sh --auto`
Expected: `second-brain` bumped to the next minor version (feat commits since the last bump).

- [ ] **Step 3: Commit the bump.**

```bash
git add .claude-plugin/marketplace.json README.md
git commit -m "chore(second-brain): bump version to <X.Y.Z>"
```

- [ ] **Step 4: Annotate the folded-in tasks and mark them done.**

Run:
```bash
for u in 02c6c391 352b98c7 c78a1d05 bcfce885; do
  task "$u" annotate "Addressed on branch capture-followup-tax (capture follow-up-tax design, 2026-10-16)"
  task "$u" done
done
```
Expected: 4 tasks completed.
