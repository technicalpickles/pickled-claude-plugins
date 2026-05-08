# Park Two-Modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Teach the `agent-meta:park` skill to produce two different artifacts based on user intent (close-out record vs continuation handoff), and teach `agent-meta:unpark` to recognize and route both correctly.

**Architecture:** Markdown-only changes to two SKILL.md files plus README and version bump. No new code, no scripts, no new files. Mode is detected at park time using a three-signal hierarchy (explicit hint → terminal-state inference → AskUserQuestion fallback) and locked into the resulting file via heading (`Wrapped:` vs `Parked:`) and filename suffix (`-wrapped.md` vs bare).

**Tech Stack:** Markdown SKILL.md prompts, marketplace.json versioning via `scripts/bump-version.sh`.

**Spec:** [`../specs/2026-05-08-park-two-modes-design.md`](../specs/2026-05-08-park-two-modes-design.md)

---

## Files Touched

- Modify: `plugins/agent-meta/skills/park/SKILL.md`: add mode detection block, replace single output template with two templates, add filename rule, expand examples
- Modify: `plugins/agent-meta/skills/unpark/SKILL.md`: add grouped listing, add wrapped-file detection and reference-mode flow
- Modify: `plugins/agent-meta/README.md`: document the two modes in the Skills table
- Modify: `.claude-plugin/marketplace.json`: bump `agent-meta` from `2.0.0` to `2.1.0` (minor, since this is a `feat`)

No new files. No scripts. Skills are markdown.

## Verification Approach

Skills are markdown prompts, not code. There is no test runner. Verification is a mental walkthrough of three scenarios against the final SKILL.md content, performed in Task 5. Each scenario asserts that the skill, given the input, would produce the expected file. The scenarios are specified upfront so they double as design documentation embedded in the plan.

---

## Task 1: Update park SKILL.md with two-mode logic

**Files:**
- Modify: `plugins/agent-meta/skills/park/SKILL.md` (full rewrite of body, frontmatter unchanged)

- [ ] **Step 1: Read current SKILL.md to confirm starting state**

Run: `cat plugins/agent-meta/skills/park/SKILL.md`
Expected: file matches what the spec describes as the "current park" template, single output shape, Resume Prompt at the bottom.

- [ ] **Step 2: Replace SKILL.md body with two-mode version**

Replace the contents of `plugins/agent-meta/skills/park/SKILL.md` with:

````markdown
---
name: park
description: Save current work context for later resumption
allowed-tools: Bash(scripts/get-session-id.sh)
---

# Park

Save the current work session. Park has two modes. Pick one, write that shape, do not mix.

## Modes

| Mode | Use when | Heading | Filename |
|------|----------|---------|----------|
| **Continuation** | Bouncing to a new session, work continues | `Parked:` | `[topic-slug].md` |
| **Close-out** | Work is done, capturing a record before walking away | `Wrapped:` | `[topic-slug]-wrapped.md` |

## Mode Detection

Pick one mode by checking three signals in order. Stop at the first one that resolves.

1. **Explicit user hint.**
   - "park, I'm done" / "wrap this up" / "park to close it out" / "park as record" → close-out
   - "park, switching sessions" / "park to continue" / "park, picking back up later" → continuation
2. **Terminal-state inference.** If all major next steps are done, no blockers remain, and the current state reads as terminal → close-out. If concrete unfinished next actions exist → continuation.
3. **Ambiguity fallback.** Use the AskUserQuestion tool with one A/B question:
   - Question: "Is this a close-out (work is done, archiving) or a continuation (planning to pick this up in a new session)?"
   - Options: "Close-out (record)" / "Continuation (handoff)"

Pick once and commit. Do not switch modes mid-write.

## Before Writing

1. Resolve session ID:
   - **Preferred:** Look for a `Session ID:` line in the PostToolUse hook context that this plugin injects when `agent-meta:park` is invoked. Use that value. A `Transcript:` line may also be present.
   - **Fallback:** Run [scripts/get-session-id.sh](scripts/get-session-id.sh) via Bash. If empty, use `unknown`.
2. Gather git branch, worktree path, files touched.
3. Resolve output location, in order:
   1. Project `CLAUDE.md` → `## Handoffs` or `## Parking` → `Location:`
   2. User `~/.claude/CLAUDE.md` → same lookup
   3. Default: `.parkinglot/` in project root (verify it is gitignored)

## Continuation Template

Use when the user is bouncing to a new session and the work continues.

~~~markdown
# Parked: [Topic]

**Parked:** [Date/time]
**Session:** [session ID]
**Branch:** [branch-name]
**Worktree:** [path if applicable]

## Resume Prompt

```
unpark [path]

[Tight, specific next-action paragraph. Names files, names skill to invoke,
names the open question to resolve. Copy-paste ready.]
```

## Current State
[What's done, what's in progress, what's blocked. Present tense.]

## Key Decisions
- [Decision + brief rationale]

## Relevant Files
- path/to/file.ts (new|modified|read)

## Next Steps
1. [Concrete next action]
2. [Concrete next action]

## Open Questions
[Optional. Things the next session needs to resolve.]
~~~

**Resume Prompt is mandatory and must be specific.** Before writing the file, check the generated prompt: if it reads as filler ("if you want to resume...", "feel free to continue...", "you could pick this up..."), regenerate it with concrete file paths, named skills to invoke, and explicit next actions. Do not write the file with a filler prompt.

Filename: `[topic-slug].md`

## Close-out Template

Use when the work is done and the user is walking away. There may be open threads, but no baton-pass.

```markdown
# Wrapped: [Topic]

**Wrapped:** [Date/time]
**Session:** [session ID]
**Branch:** [branch-name]
**Worktree:** [path if applicable]

## Outcome
[What got done. Past tense. Reference commits where applicable.]

## Key Decisions
- [Decision + brief rationale]

## Relevant Files
- path/to/file.ts (new|modified|read)

## Open Threads
[Optional. Things noticed but not done. One line each.
Surface candidates for beans, but DO NOT auto-create them.]
```

Filename: `[topic-slug]-wrapped.md`

Close-out has no Resume Prompt and no Next Steps. If you find yourself wanting to write either, the work is probably a continuation: re-check the mode.

## After Parking

For continuation:

```
Parked to `[path]`.

To resume in a new session, ask Claude:
> unpark [path]
```

For close-out:

```
Wrapped to `[path]`.

This is a close-out record. To start fresh work that builds on it, reference the file in your next session.
```
````

- [ ] **Step 3: Verify the file is well-formed**

Run: `head -5 plugins/agent-meta/skills/park/SKILL.md`
Expected: starts with the YAML frontmatter `---\nname: park\n...`

Run: `grep -c '^# ' plugins/agent-meta/skills/park/SKILL.md`
Expected: at least one top-level heading.

- [ ] **Step 4: Commit**

```bash
git add plugins/agent-meta/skills/park/SKILL.md
git commit -m "feat(agent-meta): split park into close-out and continuation modes

Park now picks between two output templates based on user intent:
- Continuation (Parked:) for handoffs to a new session
- Close-out (Wrapped:) for records of completed work

Continuation Resume Prompt promoted to top of file and made mandatory.
Close-out drops the vestigial Resume Prompt entirely.

See plugins/agent-meta/docs/specs/2026-05-08-park-two-modes-design.md"
```

---

## Task 2: Update unpark SKILL.md with grouped listing and wrapped reference mode

**Files:**
- Modify: `plugins/agent-meta/skills/unpark/SKILL.md`

- [ ] **Step 1: Read current SKILL.md to confirm starting state**

Run: `cat plugins/agent-meta/skills/unpark/SKILL.md`
Expected: a single ungrouped listing under "Find Handoff" and a single validation flow.

- [ ] **Step 2: Replace SKILL.md body with grouped-listing version**

Replace the contents of `plugins/agent-meta/skills/unpark/SKILL.md` with:

````markdown
---
name: unpark
description: Resume work from a parked handoff
---

# Unpark

Resume work from a parked handoff document, or read a wrapped close-out record as reference.

## Process

### 1. Find Handoff

Check parking locations in order:

1. Project `CLAUDE.md` → `## Handoffs` or `## Parking` → `Location:`
2. User `~/.claude/CLAUDE.md` → same lookup
3. Default: `.parkinglot/` in project root

If multiple files exist, group them by mode and list:

```
Active handoffs:
(A) jwt-authentication.md     - Parked 2026-05-06
(B) fix-login-bug.md          - Parked 2026-05-04

Wrapped (reference only):
(C) sanitation-skill-fix-wrapped.md       - Wrapped 2026-03-30
(D) confirm-dotfiles-work-role-wrapped.md - Wrapped 2026-04-12

(E) Other location
```

Detect group by filename suffix (`-wrapped.md`) and the file's first heading (`Parked:` vs `Wrapped:`). Filename and heading should agree; if they disagree, trust the heading and note the mismatch.

### 2. Branch on Mode

After the user picks a file, read it and check the first heading.

- `# Parked:` → continue with **Continuation Flow** below
- `# Wrapped:` → switch to **Reference Flow** below

### Continuation Flow

#### 2a. Read and Present

Read the handoff and present a summary:

```
Resuming: [Topic]

Parked: [Date]
Branch: [branch]

Current state: [Brief summary]

Next steps:
1. [Step 1]
2. [Step 2]
```

#### 2b. Validate

Check that the handoff is still valid:

- [ ] Git branch matches (or can be checked out)
- [ ] Worktree exists (if specified)
- [ ] Key files still exist
- [ ] Decisions still seem relevant

#### 2c. Handle Validation Results

**If valid:**

```
Validation passed. Ready to continue with: [first next step]

Proceed?
(A) Yes, continue
(B) Review the full handoff first
(C) Adjust the plan
```

**If stale or invalid:**

```
Validation found issues:
- [Issue 1]
- [Issue 2]

Options:
(A) Update handoff and try again - I'll revise based on current state
(B) Start fresh - discard this handoff
(C) Continue anyway - I understand the context has changed
```

If option A: update the handoff file with current findings, then recommend unparking again.

### Reference Flow

For `Wrapped:` files. No validation runs by default. Present the file as a reference:

```
This is a close-out record, not a handoff. Showing it as reference.

Wrapped: [topic]
Date: [...]
Outcome: [first paragraph from Outcome section]

Options:
(A) Read the full record
(B) Start fresh work building on this   ← invokes brainstorming with this doc as context
(C) Treat as continuation anyway        ← runs full validation despite the heading
```

Option (A): print the file contents as a reference, no further action.
Option (B): invoke `superpowers:brainstorming` and pass the wrapped doc's path as starting context.
Option (C): rare escape hatch. Treat the file as if it were a continuation and run the validate step from the Continuation Flow. Useful if the user wrapped something prematurely.

## Session Chains

Both `Parked:` and `Wrapped:` files include a `Session:` field. Session tracking tools can use this to link work across sessions:

```
Session A (parked) -> handoff.md -> Session B (unparked) -> parked again -> ...
Session A (wrapped) -> wrapped.md -> [end of chain, unless treated as continuation]
```

## Edge Cases

- **Branch doesn't exist:** Offer to create it or pick a different branch.
- **Files deleted:** Note in validation, may still be able to continue.
- **Handoff is very old:** Extra scrutiny on decisions, they may need revisiting.
- **Filename/heading mismatch:** Trust the heading. Note the mismatch to the user.
- **Legacy `Parked:` file with old shape (Resume Prompt at bottom):** Works fine. The validation flow does not depend on section order.
````

- [ ] **Step 3: Verify the file is well-formed**

Run: `head -5 plugins/agent-meta/skills/unpark/SKILL.md`
Expected: starts with the YAML frontmatter `---\nname: unpark\n...`

Run: `grep -c '^# ' plugins/agent-meta/skills/unpark/SKILL.md`
Expected: at least one top-level heading.

- [ ] **Step 4: Commit**

```bash
git add plugins/agent-meta/skills/unpark/SKILL.md
git commit -m "feat(agent-meta): teach unpark about wrapped close-out files

Unpark now groups parking-lot entries into 'Active handoffs' and
'Wrapped (reference only)'. Wrapped files trigger reference mode
(no validation, options to read / start fresh / treat as continuation)
instead of the standard validate-and-resume flow."
```

---

## Task 3: Update agent-meta README

**Files:**
- Modify: `plugins/agent-meta/README.md`

- [ ] **Step 1: Read current README**

Run: `cat plugins/agent-meta/README.md`
Expected: existing Skills table with three rows.

- [ ] **Step 2: Replace the Skills table and add a Modes subsection**

Find this block in `plugins/agent-meta/README.md`:

```markdown
## Skills

| Skill | Description |
|-------|-------------|
| `agent-meta:park` | Save current work context for later resumption |
| `agent-meta:unpark` | Resume work from a parked handoff |
| `agent-meta:snapshot` | Capture current session state (inline or with save) |

Invoke by asking naturally ("park this session", "unpark docs/handoffs/foo.md") or with the fully qualified slash form (`/agent-meta:park`).
```

Replace it with:

```markdown
## Skills

| Skill | Description |
|-------|-------------|
| `agent-meta:park` | Save current work context. Two modes: **continuation** (handoff to new session) and **close-out** (record of completed work). |
| `agent-meta:unpark` | Resume work from a parked handoff, or read a wrapped close-out as reference. |
| `agent-meta:snapshot` | Capture current session state (inline or with save). In-flow checkpoint, not a walking-away artifact. |

Invoke by asking naturally ("park this session", "wrap this up", "unpark docs/handoffs/foo.md") or with the fully qualified slash form (`/agent-meta:park`).

### Park modes

`park` produces two distinct artifacts:

- **Continuation** (`Parked:` heading, `[topic].md` filename): for handoffs to a new session. The Resume Prompt is the centerpiece: tight, specific, copy-paste ready.
- **Close-out** (`Wrapped:` heading, `[topic]-wrapped.md` filename): for records of completed work. No Resume Prompt; an "Outcome" section in past tense and an optional "Open Threads" list.

Mode is picked at park time from your phrasing ("park to continue" vs "wrap this up"), inferred from the work's state, or asked if ambiguous.
```

- [ ] **Step 3: Verify the file rendered correctly**

Run: `grep -A2 '^## Skills' plugins/agent-meta/README.md | head`
Expected: shows the new table with both modes mentioned.

- [ ] **Step 4: Commit**

```bash
git add plugins/agent-meta/README.md
git commit -m "docs(agent-meta): document park's two modes in README"
```

---

## Task 4: Bump version

**Files:**
- Modify: `.claude-plugin/marketplace.json` (via script)

- [ ] **Step 1: Run the bump script**

Run: `./scripts/bump-version.sh agent-meta minor`
Expected: script reports `agent-meta: 2.0.0 → 2.1.0` (or similar) and updates `.claude-plugin/marketplace.json`.

- [ ] **Step 2: Verify version landed**

Run: `python3 -c "import json; m=json.load(open('.claude-plugin/marketplace.json')); print([p['version'] for p in m['plugins'] if p['name']=='agent-meta'][0])"`
Expected: `2.1.0`

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore(agent-meta): bump version to 2.1.0"
```

---

## Task 5: Manual verification walkthrough

**Files:** None modified. This task is a checklist.

The three scenarios below are mental walkthroughs against the final SKILL.md content. For each, simulate what the skill would do given the inputs and confirm the output matches the expected shape.

- [ ] **Scenario 1: Explicit close-out hint**

  Input: User says "park this, I'm done with the sanitation skill fix, it's committed."

  Expected behavior:
  1. Park reads "I'm done" → close-out mode (signal 1).
  2. No AskUserQuestion fired.
  3. Output file: `[parking-lot]/sanitation-skill-fix-wrapped.md`
  4. Heading: `# Wrapped: Sanitation skill fix`
  5. No Resume Prompt section. No Next Steps section.
  6. Outcome section in past tense, references the commit.

  Verify by re-reading park SKILL.md and confirming the close-out template would produce this shape.

- [ ] **Scenario 2: Explicit continuation hint with concrete next action**

  Input: User says "park, I'm switching sessions. Need to invoke writing-plans next on the spec at projects/foo/spec.md."

  Expected behavior:
  1. Park reads "switching sessions" → continuation mode (signal 1).
  2. Output file: `[parking-lot]/foo-spec-writing-plans.md`
  3. Heading: `# Parked: foo spec writing-plans`
  4. Resume Prompt section appears immediately after front matter.
  5. Resume Prompt code block names `superpowers:writing-plans` and the spec path explicitly.
  6. Next Steps section lists the writing-plans invocation.

  Verify the prompt is specific (no "if you want to..." filler).

- [ ] **Scenario 3: Ambiguous park → AskUserQuestion fires**

  Input: User says "park this" with no other context, and the work has both completed pieces and unfinished pieces.

  Expected behavior:
  1. Park finds no explicit hint (signal 1 fails).
  2. Terminal-state inference is ambiguous (signal 2 fails).
  3. AskUserQuestion fires with the A/B question from SKILL.md.
  4. Skill waits for the answer, then proceeds with the chosen template.

  Verify the AskUserQuestion call matches what SKILL.md specifies.

- [ ] **Scenario 4: Unpark on a wrapped file**

  Input: User says "unpark sanitation-skill-fix-wrapped.md".

  Expected behavior:
  1. Unpark detects `-wrapped.md` suffix and reads the file.
  2. First heading is `# Wrapped:` → Reference Flow.
  3. No validation runs.
  4. Presents Outcome paragraph + A/B/C options.

  Verify by re-reading unpark SKILL.md.

- [ ] **Scenario 5: Unpark listing with mixed parking lot**

  Input: User says "unpark" with no path.

  Expected behavior:
  1. Unpark lists files from the parking lot.
  2. Files are grouped: "Active handoffs:" first, "Wrapped (reference only):" second.
  3. Each entry shows filename + parked/wrapped date.

- [ ] **Sign-off: all scenarios pass**

If any scenario reveals a gap, fix the relevant SKILL.md inline and recommit before moving on.

---

## Self-Review Checklist (run before handing the plan to an executor)

- [ ] Every spec section has a corresponding task or is explicitly noted as "no change required" (snapshot, output location resolution, session ID injection).
- [ ] No placeholder text in any task. Every code block contains the actual content.
- [ ] Filename suffix is `-wrapped.md` (consistent across spec, park, unpark, README, and verification scenarios).
- [ ] Heading is `Wrapped:` (consistent across spec, park, unpark).
- [ ] Version bump is a `feat` → minor (2.0.0 → 2.1.0), per repo conventional-commit rules.
- [ ] Existing `.parkinglot/*.md` files in the spec are not modified or migrated.
