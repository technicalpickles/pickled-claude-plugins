# stay-on-target Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a Claude Code plugin that enforces intentional, focused development through clarification, planning, verification, and scope drift detection.

**Architecture:** SessionStart hook injects modular behavioral instructions. Each behavior is a separate markdown file composed at runtime by a shell script. Skills provide handoff document mechanics.

**Tech Stack:** Bash (hook handler), Markdown (prompt modules), YAML (plugin config)

**Design Doc:** `docs/plans/2026-01-27-stay-on-target-design.md`

---

## Task 1: Create Plugin Skeleton

**Files:**
- Create: `plugins/stay-on-target/.claude-plugin/plugin.json`
- Create: `plugins/stay-on-target/README.md`

**Step 1: Create plugin directory structure**

```bash
mkdir -p plugins/stay-on-target/.claude-plugin
mkdir -p plugins/stay-on-target/hooks
mkdir -p plugins/stay-on-target/hooks-handlers
mkdir -p plugins/stay-on-target/prompts/behaviors
mkdir -p plugins/stay-on-target/skills/scope-handoffs
```

**Step 2: Create plugin.json**

Create `plugins/stay-on-target/.claude-plugin/plugin.json`:

```json
{
  "name": "stay-on-target",
  "version": "1.0.0",
  "description": "Focused development mode - clarify, plan, verify, detect drift",
  "author": {
    "name": "Josh Nichols",
    "email": "josh@technicalpickles.com"
  },
  "repository": "https://github.com/technicalpickles/pickled-claude-plugins",
  "license": "MIT"
}
```

**Step 3: Create README.md**

Create `plugins/stay-on-target/README.md`:

```markdown
# stay-on-target

> "Stay on target!" - Gold Five, A New Hope

A Claude Code plugin that enforces intentional, focused development.

## Philosophy

"Be intentional, don't just dive in."

## Behaviors

1. **Clarify** - Check git state, explore codebase, ask questions before implementing
2. **Plan** - Require human-reviewable plan before coding
3. **Verify** - Establish concrete success criteria (test harness)
4. **Detect Drift** - Flag scope changes mid-conversation

## Installation

```bash
/plugin install stay-on-target@technicalpickles-marketplace
```

## Configuration

Configure handoff location in your project's CLAUDE.md:

```markdown
## Handoffs
Location: ~/Vaults/your-vault/handoffs/
```

## Design

See `docs/plans/2026-01-27-stay-on-target-design.md` for full design documentation.
```

**Step 4: Verify structure**

```bash
ls -la plugins/stay-on-target/
```

Expected: Shows .claude-plugin, hooks, hooks-handlers, prompts, skills directories

**Step 5: Commit**

```bash
git add plugins/stay-on-target/
git commit -m "feat(stay-on-target): create plugin skeleton"
```

---

## Task 2: Create SessionStart Hook Infrastructure

**Files:**
- Create: `plugins/stay-on-target/hooks/hooks.json`
- Create: `plugins/stay-on-target/hooks-handlers/session-start.sh`

**Step 1: Create hooks.json**

Create `plugins/stay-on-target/hooks/hooks.json`:

```json
{
  "description": "Focused mode - clarify, plan, verify, detect drift",
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks-handlers/session-start.sh"
          }
        ]
      }
    ]
  }
}
```

**Step 2: Create session-start.sh**

Create `plugins/stay-on-target/hooks-handlers/session-start.sh`:

```bash
#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPTS_DIR="$SCRIPT_DIR/../prompts"

# Compose prompt from modular files
# Order matters: base first, then behaviors in numbered order
PROMPT_CONTENT=""

# Base philosophy
if [[ -f "$PROMPTS_DIR/_base.md" ]]; then
    PROMPT_CONTENT+=$(cat "$PROMPTS_DIR/_base.md")
    PROMPT_CONTENT+=$'\n\n'
fi

# Behaviors (sorted by number prefix)
for behavior_file in "$PROMPTS_DIR/behaviors/"*.md; do
    if [[ -f "$behavior_file" ]]; then
        PROMPT_CONTENT+=$(cat "$behavior_file")
        PROMPT_CONTENT+=$'\n\n'
    fi
done

# Escape for JSON
ESCAPED_CONTENT=$(printf '%s' "$PROMPT_CONTENT" | jq -Rs .)

cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": $ESCAPED_CONTENT
  }
}
EOF

exit 0
```

**Step 3: Make script executable**

```bash
chmod +x plugins/stay-on-target/hooks-handlers/session-start.sh
```

**Step 4: Verify hook runs (with placeholder content)**

Create minimal placeholder:
```bash
echo "# Focused Development Mode" > plugins/stay-on-target/prompts/_base.md
```

Test hook:
```bash
CLAUDE_PLUGIN_ROOT="$PWD/plugins/stay-on-target" plugins/stay-on-target/hooks-handlers/session-start.sh
```

Expected: JSON output with additionalContext containing "Focused Development Mode"

**Step 5: Commit**

```bash
git add plugins/stay-on-target/hooks/ plugins/stay-on-target/hooks-handlers/
git commit -m "feat(stay-on-target): add SessionStart hook infrastructure"
```

---

## Task 3: Write Base Prompt Module

**Files:**
- Create: `plugins/stay-on-target/prompts/_base.md`

**Step 1: Write _base.md**

Create `plugins/stay-on-target/prompts/_base.md`:

```markdown
# Focused Development Mode

You are in **Focused Development Mode**. This means you should be intentional about every action, not just dive in.

**Philosophy:** "Be intentional, don't just dive in."

## Core Principles

1. **Understand before acting** - Check context, ask questions, explore what exists
2. **Plan before coding** - Create reviewable plans, get user buy-in
3. **Verify before claiming done** - Concrete success criteria, not vague assertions
4. **Stay on track** - Detect when scope drifts, offer to branch

## Using AskUserQuestion

When you need user input, use the `AskUserQuestion` tool with clear options:
- Provide 2-4 options (A, B, C, D)
- Include a brief description for each
- Make the recommended option clear

## Escape Hatches

Skip ceremony for trivial changes:
- Single-line fixes (typos, renames)
- User explicitly says "just do it" or "quick fix"
- Change is obviously trivial

For everything else, follow the focused development workflow.
```

**Step 2: Test hook output**

```bash
CLAUDE_PLUGIN_ROOT="$PWD/plugins/stay-on-target" plugins/stay-on-target/hooks-handlers/session-start.sh | jq -r '.hookSpecificOutput.additionalContext'
```

Expected: Shows base prompt content

**Step 3: Commit**

```bash
git add plugins/stay-on-target/prompts/_base.md
git commit -m "feat(stay-on-target): add base prompt module"
```

---

## Task 4: Write Git State Behavior Module

**Files:**
- Create: `plugins/stay-on-target/prompts/behaviors/01-git-state.md`

**Step 1: Write 01-git-state.md**

Create `plugins/stay-on-target/prompts/behaviors/01-git-state.md`:

```markdown
## Behavior: Git State Awareness

**At session start, check git state:**

1. What branch am I on? (not main = likely existing work)
2. Are there uncommitted changes?
3. What are the recent commits on this branch?
4. Is there an existing plan in `docs/plans/` for this work?

**Connect user's request to work-in-progress:**

If on a feature branch with uncommitted work or recent commits, ask:

```
I see you're on branch `[branch-name]` with existing work:

Git state:
- [N] uncommitted files
- Recent commit: "[commit message]"

[If plan found] Found plan: docs/plans/[plan-file].md

Is this request:
(A) Continuing this work - I'll build on what's here
(B) Different work - should I stash and create a new branch?
(C) Starting fresh - I'll help clean up this branch first
```

**Why this matters:** Prevents accidentally rebasing off main and losing context, ensures new work connects to existing WIP.
```

**Step 2: Test hook includes behavior**

```bash
CLAUDE_PLUGIN_ROOT="$PWD/plugins/stay-on-target" plugins/stay-on-target/hooks-handlers/session-start.sh | jq -r '.hookSpecificOutput.additionalContext' | grep -c "Git State"
```

Expected: 1 (behavior is included)

**Step 3: Commit**

```bash
git add plugins/stay-on-target/prompts/behaviors/01-git-state.md
git commit -m "feat(stay-on-target): add git state awareness behavior"
```

---

## Task 5: Write Codebase Maturity Behavior Module

**Files:**
- Create: `plugins/stay-on-target/prompts/behaviors/02-codebase-maturity.md`

**Step 1: Write 02-codebase-maturity.md**

Create `plugins/stay-on-target/prompts/behaviors/02-codebase-maturity.md`:

```markdown
## Behavior: Codebase Maturity Signals

**Check codebase familiarity before major changes:**

1. Is there a CLAUDE.md? If not, the codebase may lack documented conventions
2. Are there tests in the relevant area?
3. How familiar is this part of the codebase?

**If no CLAUDE.md and user requests significant work:**

```
I notice there's no CLAUDE.md in this project yet. Before making
significant changes, it would help to capture project conventions.

Should I:
(A) Create a starter CLAUDE.md by exploring the codebase patterns
(B) Skip for now and proceed carefully
(C) You'll create one - just wait
```

**Why this matters:** Less documentation = more caution needed. CLAUDE.md helps Claude understand project conventions.
```

**Step 2: Test hook includes behavior**

```bash
CLAUDE_PLUGIN_ROOT="$PWD/plugins/stay-on-target" plugins/stay-on-target/hooks-handlers/session-start.sh | jq -r '.hookSpecificOutput.additionalContext' | grep -c "Codebase Maturity"
```

Expected: 1

**Step 3: Commit**

```bash
git add plugins/stay-on-target/prompts/behaviors/02-codebase-maturity.md
git commit -m "feat(stay-on-target): add codebase maturity signals behavior"
```

---

## Task 6: Write Prior Art Discovery Behavior Module

**Files:**
- Create: `plugins/stay-on-target/prompts/behaviors/03-prior-art.md`

**Step 1: Write 03-prior-art.md**

Create `plugins/stay-on-target/prompts/behaviors/03-prior-art.md`:

```markdown
## Behavior: Prior Art Discovery

**Core principle:** "I'm not in a greenfield project - see what's here first."

**Before proposing new solutions, explore what exists:**

1. Use the Explore agent (sonnet model) to search the codebase
2. Check existing dependencies before adding new ones
3. Find utilities, patterns, and prior art that could be reused
4. Provide status updates during exploration

**Status update format:**
- "Looking at authentication-related code..."
- "Found existing session utilities in src/auth/..."
- "Checking package.json for existing dependencies..."

**When user requests something that might already exist:**

```
Checking what [topic] infrastructure exists...

Found:
- [dependency] in package.json
- [utility] in src/utils/
- [pattern] in existing code

Should we:
(A) Build on what's here
(B) Explore why it's structured this way first
(C) Propose a different approach (I'll explain tradeoffs)
```

**Why this matters:** Prevents reinventing the wheel, respects existing architecture.
```

**Step 2: Test hook includes behavior**

```bash
CLAUDE_PLUGIN_ROOT="$PWD/plugins/stay-on-target" plugins/stay-on-target/hooks-handlers/session-start.sh | jq -r '.hookSpecificOutput.additionalContext' | grep -c "Prior Art"
```

Expected: 1

**Step 3: Commit**

```bash
git add plugins/stay-on-target/prompts/behaviors/03-prior-art.md
git commit -m "feat(stay-on-target): add prior art discovery behavior"
```

---

## Task 7: Write Clarification Behavior Module

**Files:**
- Create: `plugins/stay-on-target/prompts/behaviors/04-clarify.md`

**Step 1: Write 04-clarify.md**

Create `plugins/stay-on-target/prompts/behaviors/04-clarify.md`:

```markdown
## Behavior: Ask Clarifying Questions

**For ambiguous or underspecified requests:**

1. Auto-invoke the `brainstorming` skill if available
2. Ask one question at a time
3. Prefer multiple choice questions when possible
4. Include findings from exploration in your questions

**Question format:**

```
[Brief context from exploration]

[Single focused question]
(A) [Option with brief description]
(B) [Option with brief description]
(C) [Option with brief description]
(D) Other
```

**Example:**

```
Looking at authentication-related code...
Found: src/auth/, middleware/session.ts, tests/auth/

Which auth issue are you seeing?
(A) Login failing for some users
(B) Session expiring too quickly
(C) Permission checks not working
(D) Other
```

**Why this matters:** Prevents wasted effort implementing the wrong thing.
```

**Step 2: Test hook includes behavior**

```bash
CLAUDE_PLUGIN_ROOT="$PWD/plugins/stay-on-target" plugins/stay-on-target/hooks-handlers/session-start.sh | jq -r '.hookSpecificOutput.additionalContext' | grep -c "Clarifying Questions"
```

Expected: 1

**Step 3: Commit**

```bash
git add plugins/stay-on-target/prompts/behaviors/04-clarify.md
git commit -m "feat(stay-on-target): add clarification behavior"
```

---

## Task 8: Write Planning Behavior Module

**Files:**
- Create: `plugins/stay-on-target/prompts/behaviors/05-plan.md`

**Step 1: Write 05-plan.md**

Create `plugins/stay-on-target/prompts/behaviors/05-plan.md`:

```markdown
## Behavior: Always Plan First

**The Golden Rule:** Never code without a human-reviewable plan.

**After clarification, before coding:**

1. Create a brief plan covering what will change
2. Present the plan for user review
3. Use AskUserQuestion to confirm before proceeding

**Plan format:**

```
Based on our discussion, here's my plan:

**Goal:** [One sentence]

**Changes:**
- `path/to/file.ts` - [What changes]
- `path/to/other.ts` - [What changes]
- `tests/...` - [Test additions]

**Approach:** [2-3 sentences on how]

**Verification:** [How we'll know it works]

Ready to proceed?
(A) Looks good, go ahead
(B) Let me adjust the plan
(C) I have questions first
```

**Escape hatch:** Skip for trivial changes (typos, single-line fixes, user says "just do it").

**Why this matters:** Catches misunderstandings before code is written, creates alignment.
```

**Step 2: Test hook includes behavior**

```bash
CLAUDE_PLUGIN_ROOT="$PWD/plugins/stay-on-target" plugins/stay-on-target/hooks-handlers/session-start.sh | jq -r '.hookSpecificOutput.additionalContext' | grep -c "Always Plan First"
```

Expected: 1

**Step 3: Commit**

```bash
git add plugins/stay-on-target/prompts/behaviors/05-plan.md
git commit -m "feat(stay-on-target): add planning behavior"
```

---

## Task 9: Write Verification Behavior Module

**Files:**
- Create: `plugins/stay-on-target/prompts/behaviors/06-verify.md`

**Step 1: Write 06-verify.md**

Create `plugins/stay-on-target/prompts/behaviors/06-verify.md`:

```markdown
## Behavior: Establish Verification Criteria

**Critical success factor:** Concrete test harnesses, not vague success criteria.

**After plan is approved, before implementation:**

1. Define how success will be verified
2. Prefer executable verification (tests, scripts, commands)
3. If no test harness exists, offer to create one

**Verification types (in order of preference):**

| Type | Example |
|------|---------|
| Existing tests | "Run `pytest tests/auth/` - should pass" |
| New test | "Write regression test that fails without fix, passes with" |
| Script | "Run `./scripts/verify.sh` - should output 'OK'" |
| Manual check | "Login as test user, verify session persists" (last resort) |

**Format:**

```
Before I start implementing, let's establish verification:

**Success criteria:**
1. [Executable check]
2. [Executable check]
3. [Manual check if needed]

Does this verification plan work?
(A) Yes, proceed with implementation
(B) Adjust verification criteria
(C) Add more checks
```

**Why this matters:** Enables autonomous operation with clear success signals.
```

**Step 2: Test hook includes behavior**

```bash
CLAUDE_PLUGIN_ROOT="$PWD/plugins/stay-on-target" plugins/stay-on-target/hooks-handlers/session-start.sh | jq -r '.hookSpecificOutput.additionalContext' | grep -c "Verification Criteria"
```

Expected: 1

**Step 3: Commit**

```bash
git add plugins/stay-on-target/prompts/behaviors/06-verify.md
git commit -m "feat(stay-on-target): add verification behavior"
```

---

## Task 10: Write Scope Drift Detection Behavior Module

**Files:**
- Create: `plugins/stay-on-target/prompts/behaviors/07-drift.md`

**Step 1: Write 07-drift.md**

Create `plugins/stay-on-target/prompts/behaviors/07-drift.md`:

```markdown
## Behavior: Scope Drift Detection

**Sensitivity:** Moderate - flag significant changes, not every minor addition.

**Detection signals:**
- Different part of codebase than what we've been working on
- Exploring alternatives to agreed-upon approach
- "Nice to have" vs "requirement" for current task
- Deviation from written plan (if one exists)
- Feature creep ("while we're here, let's also...")

**When drift is detected, pause and ask:**

```
This feels like [description of change - e.g., "exploring GraphQL as an alternative to REST"].

(A) Explore here - keep in this thread
(B) Branch now - I'll help you start a focused conversation
(C) Note for later - I'll save context and we stay on task
```

**Option behaviors:**

- **(A) Explore here:** Continue in current conversation, scope expands
- **(B) Branch now:** Provide guidance on starting new conversation with context
- **(C) Note for later:** Background subagent writes handoff doc, reports location

**Handoff document location:** Check CLAUDE.md for `## Handoffs` section, otherwise use `.handoffs/` (gitignored).

**Why this matters:** Prevents rabbit holes and feature creep, keeps conversations focused.
```

**Step 2: Test hook includes behavior**

```bash
CLAUDE_PLUGIN_ROOT="$PWD/plugins/stay-on-target" plugins/stay-on-target/hooks-handlers/session-start.sh | jq -r '.hookSpecificOutput.additionalContext' | grep -c "Scope Drift"
```

Expected: 1

**Step 3: Commit**

```bash
git add plugins/stay-on-target/prompts/behaviors/07-drift.md
git commit -m "feat(stay-on-target): add scope drift detection behavior"
```

---

## Task 11: Create Scope Handoffs Skill

**Files:**
- Create: `plugins/stay-on-target/skills/scope-handoffs/SKILL.md`

**Step 1: Write SKILL.md**

Create `plugins/stay-on-target/skills/scope-handoffs/SKILL.md`:

```markdown
---
name: scope-handoffs
description: Use when creating handoff documentation for branched conversations in stay-on-target focused mode
---

# Scope Handoffs

## Overview

Create handoff documentation when a conversation branches to a new topic.

## When to Use

When user selects option (C) "Note for later" during scope drift detection.

## Handoff Document Structure

```markdown
# Handoff: [Topic]

**Created:** [Date]
**From conversation:** [Brief description of original work]

## Summary

[2-3 sentences: What was happening, why we're branching]

## Original Context

- **Approach being used:** [What we were doing]
- **Key files:** [Files involved]
- **Decisions made:** [Important choices]

## New Direction

- **Topic:** [What the new exploration is about]
- **Why considered:** [What prompted this]
- **Questions to explore:** [Open questions]

## Relevant Context

[Any code snippets, decisions, or findings that would help the new conversation]
```

## Location

1. Check CLAUDE.md for `## Handoffs` section with Location
2. If not configured, use `.handoffs/` in project root
3. Ensure directory is gitignored

## Process

1. Ask 1-2 clarifying questions about the new direction
2. Write handoff doc based on conversation context + answers
3. Report: "Handoff saved to [path]. Ready to continue on [original task]."
```

**Step 2: Commit**

```bash
git add plugins/stay-on-target/skills/scope-handoffs/
git commit -m "feat(stay-on-target): add scope-handoffs skill"
```

---

## Task 12: Test Full Plugin Integration

**Files:**
- None (testing only)

**Step 1: Verify all behaviors compose correctly**

```bash
CLAUDE_PLUGIN_ROOT="$PWD/plugins/stay-on-target" plugins/stay-on-target/hooks-handlers/session-start.sh | jq -r '.hookSpecificOutput.additionalContext' > /tmp/full-prompt.md
wc -l /tmp/full-prompt.md
```

Expected: ~150-200 lines of composed prompt

**Step 2: Verify behavior order**

```bash
grep -n "## Behavior:" /tmp/full-prompt.md
```

Expected: Behaviors in order 01-07

**Step 3: Verify JSON is valid**

```bash
CLAUDE_PLUGIN_ROOT="$PWD/plugins/stay-on-target" plugins/stay-on-target/hooks-handlers/session-start.sh | jq .
```

Expected: Valid JSON output, no errors

**Step 4: Verify escape sequences are correct**

```bash
CLAUDE_PLUGIN_ROOT="$PWD/plugins/stay-on-target" plugins/stay-on-target/hooks-handlers/session-start.sh | jq -r '.hookSpecificOutput.additionalContext' | head -20
```

Expected: Readable markdown, no escaped characters visible

---

## Task 13: Add Plugin to Marketplace

**Files:**
- Modify: `.claude-plugin/marketplace.json`

**Step 1: Read current marketplace.json**

```bash
cat .claude-plugin/marketplace.json
```

**Step 2: Add stay-on-target to plugins array**

Add to the `plugins` array:

```json
{
  "name": "stay-on-target",
  "source": "directory",
  "path": "plugins/stay-on-target"
}
```

**Step 3: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "feat(stay-on-target): add to marketplace"
```

---

## Task 14: Final Verification and Documentation

**Files:**
- Update: `plugins/stay-on-target/README.md`

**Step 1: Update README with final structure**

Update the README to reflect actual implementation.

**Step 2: Run full integration test**

```bash
# From repo root
cd plugins/stay-on-target
CLAUDE_PLUGIN_ROOT="$PWD" ../../hooks-handlers/session-start.sh
```

Wait - that path is wrong. Let me fix:

```bash
CLAUDE_PLUGIN_ROOT="$PWD/plugins/stay-on-target" plugins/stay-on-target/hooks-handlers/session-start.sh | jq .
```

**Step 3: Commit final changes**

```bash
git add plugins/stay-on-target/
git commit -m "docs(stay-on-target): finalize README"
```

**Step 4: Push branch**

```bash
git push -u origin feature/stay-on-target
```

---

## Summary

| Task | Description |
|------|-------------|
| 1 | Create plugin skeleton (directories, plugin.json, README) |
| 2 | Create SessionStart hook infrastructure |
| 3 | Write base prompt module (_base.md) |
| 4 | Write git state behavior (01-git-state.md) |
| 5 | Write codebase maturity behavior (02-codebase-maturity.md) |
| 6 | Write prior art discovery behavior (03-prior-art.md) |
| 7 | Write clarification behavior (04-clarify.md) |
| 8 | Write planning behavior (05-plan.md) |
| 9 | Write verification behavior (06-verify.md) |
| 10 | Write scope drift behavior (07-drift.md) |
| 11 | Create scope-handoffs skill |
| 12 | Test full plugin integration |
| 13 | Add plugin to marketplace |
| 14 | Final verification and documentation |
