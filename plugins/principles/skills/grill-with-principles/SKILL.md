---
name: grill-with-principles
description: Walk a depth-first decision tree anchored to a project's documented principles before brainstorming opens options. Reads docs/agents/principles.md (or probes docs/principles.md and docs/ops-principles.md directly), shortlists principles relevant to the topic, asks one question at a time with a recommended answer per question, surfaces conflicts emergently, and outputs a brief that downstream brainstorming or planning can consume. Use when starting design work and the project has principles documented; redirects to setup-principles otherwise. Auto-routes from phrases like "grill me with principles", "anchor this to the principles", "what principles bear on this".
---

# Grill with Principles

Walk a depth-first decision tree using the project's principles as the tree roots, before brainstorming opens. The mechanism is grill-me's: one question at a time, recommended answer per node, explore the codebase instead of asking when the answer is there. The anchor is principles, not generic decisions.

## Why this exists

Brainstorming-style breadth-first menus drag conversations toward implementation variants. Depth-first walking with principle anchoring stays at the *why* level. Principles loaded as upfront context are necessary but not sufficient: they need to act as a forcing function during decision moments, not as wallpaper.

## Process

### 1. Discover principles

- Read `docs/agents/principles.md` if it exists. This is the canonical config written by `setup-principles`.
- Otherwise probe `docs/principles.md` and `docs/ops-principles.md` directly.
- Resolve all paths against `git rev-parse --show-toplevel` so worktree invocations find the right files.
- If nothing is found, ask: *"No principles configured. Skip principle-anchoring, or run `setup-principles` first?"* and exit cleanly. Do not pretend to grill without principles. The whole point is anchoring.

### 2. Read and shortlist

- Read all configured principle files into your working set.
- Based on the user's stated topic and visible context (recent commits, branch name, files mentioned, current cwd), propose a shortlist by number and name.
- Cite by number AND name so the user can react fast: *"I think principles 3 (agent proposes), 4 (capture vs triage), and 9 (resilience) bear on this. Anything I'm missing?"*
- If the topic touches a named domain in the domain map, include the domain-specific principles for that domain.
- Wait for the user to confirm, add, or remove before moving on.

### 3. Confirm and walk

Walk the shortlist depth-first, one principle at a time.

For each principle:
- Frame the question that would make this principle bite for the current design. Don't ask abstract questions; ask the concrete one this principle implies.
- Provide a recommended answer, drawing from the `Where:` examples in the principles file when relevant. If the principles file has correction cases for this principle, mention them as part of the recommendation when relevant.
- Wait for the user to confirm, adjust, or reject.
- One question at a time. Never present a menu.
- Cite the principle by number explicitly so cross-references stay easy: *"Per #3..."*

Carry constraints forward: if principle 3 established that 'agents propose, humans confirm', use that boundary when asking the principle 9 question instead of re-asking whether agents should propose. Don't re-ask what's already settled.

### 4. Surface conflicts emergently

When two principles pull opposite ways on the same decision, surface the conflict explicitly. Do **not** recommend a resolution. These are exactly the kind of question that needs the user's judgment, not the agent's.

Example conflicts the brineworks file already shows:
- #5 "defer until concrete need" vs #4 "capture is frictionless": capture features get built before they're "needed".
- #13 "design ceremony matches deployment model" vs any principle that imports multi-user discipline.

Frame: *"#5 says defer, #4 says capture. Which dominates here?"*

### 5. Cite correction cases

When the principles file documents correction cases or known violations (however they are formatted), surface them when the topic resembles the original pattern. Don't just cite; ask whether the same shape applies:

> "Principle 8 had a leak in [context from principles file]. Does the same pattern apply here?"

### 6. Output the brief

When the tree is walked or visibly stabilized, synthesize a brief inline. Include only the fields that apply; omit any that are empty (e.g., omit 'Active conflicts' if none surfaced):

```
## Principle brief: <topic>

**Anchored to:** principles 3, 4, 9

**Resolved:**
- Per #3: agent proposes, human confirms at the X boundary
- Per #4: capture lands raw at Y; filtering happens in triage step Z

**Open at brainstorm time:** ...

**Honored constraints:** ...

**Active conflicts (need user resolution):** ...
```

Always output inline. Offer to write to `docs/plans/YYYY-MM-DD-<topic>-principle-brief.md` when the brief is non-trivial. Never auto-write. The brief is a starting point, and the user may want to edit it before downstream skills consume it.

## Mode rules (carried from grill-me)

- One question at a time. Never present a menu.
- Always include a recommended answer, except when surfacing a principle conflict.
- Explore the codebase or principles file instead of asking when the answer is there.
- Stay at the intent level. If the user pulls toward implementation, redirect:

  > "That's a brainstorming question. Want to settle the principle 3 boundary first, or jump?"

- Cite principles by number, always. The numbering is the lingua franca that makes cross-references and correction-case citations cheap.

## What this skill does not do

- Generate option menus. That's `superpowers:brainstorming`'s job, downstream.
- Recommend resolutions to principle conflicts.
- Write or amend the principles file. That's a future capture-side skill (`principle-sweep`), out of scope for v1.
- Handle non-markdown principle files. The skill is format-tolerant for markdown but does not parse other formats.
