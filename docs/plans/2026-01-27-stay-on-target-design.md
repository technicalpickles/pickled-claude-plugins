# stay-on-target Plugin Design

> "Stay on target!" - Gold Five, A New Hope

## Overview

A Claude Code plugin that enforces intentional, focused development by:
1. **Clarifying** ambiguous requests before diving into implementation
2. **Planning** - requiring a human-reviewable plan before coding
3. **Verifying** - establishing concrete success criteria (test harness)
4. **Detecting drift** mid-conversation and offering to branch off

Philosophy: "Be intentional, don't just dive in."

## Problem Statement

When a user says something ambiguous like "fix the blah," Claude often jumps straight into implementation. This wastes time when requirements aren't clear.

Even with clear requirements, Claude may start coding without a reviewable plan, leading to misalignment that's expensive to fix later.

Without concrete verification criteria, Claude produces code that "looks right" but doesn't actually work. The user becomes the only feedback loop.

Mid-conversation, users may ask questions that drift from the original scope (e.g., switching from REST to GraphQL exploration). Without intervention, this leads to rabbit holes and feature creep.

## Goals

- **Clarify first**: Pause on ambiguous requests to ask questions before implementing
- **Always plan**: Require a human-reviewable plan before writing code
- **Establish verification**: Define concrete success criteria (test harness) before implementation
- **Detect drift**: Flag scope changes with moderate sensitivity
- **Offer structure**: Use AskUserQuestion for smooth interventions (click, don't type)
- **Enable handoffs**: Create documentation when branching conversations

## Non-Goals

- Replacing the default Claude Code system prompt (additive only)
- Strict scope enforcement (moderate sensitivity, not aggressive)
- Automatic branching without user consent
- Blocking quick fixes that don't need planning (single-line changes, typos)

## Design

### The Focused Development Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Request                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
               ┌──────────────────────────────┐
               │  Trivial change?             │
               │  (typo, single line, etc.)   │
               └──────────────────────────────┘
                    │                    │
                   YES                  NO
                    │                    │
                    ▼                    ▼
             ┌──────────┐    ┌─────────────────────────┐
             │ Just do  │    │ BEHAVIOR 1: CLARIFY     │
             │ it       │    │ - Explore agent (bg)    │
             │          │    │ - Ask questions         │
             └──────────┘    │ - Status updates        │
                             └─────────────────────────┘
                                          │
                                          ▼
                             ┌─────────────────────────┐
                             │ BEHAVIOR 2: PLAN        │
                             │ - Present plan          │
                             │ - User reviews          │
                             │ - AskUserQuestion       │
                             └─────────────────────────┘
                                          │
                                          ▼
                             ┌─────────────────────────┐
                             │ BEHAVIOR 3: VERIFY      │
                             │ - Define success        │
                             │ - Test harness          │
                             │ - Executable criteria   │
                             └─────────────────────────┘
                                          │
                                          ▼
                             ┌─────────────────────────┐
                             │ IMPLEMENTATION          │
                             │ (normal Claude Code)    │
                             └─────────────────────────┘
                                          │
                    ┌─────────────────────┴─────────────────────┐
                    │                                           │
                    ▼                                           ▼
         ┌───────────────────┐                      ┌───────────────────┐
         │ On track          │                      │ BEHAVIOR 4: DRIFT │
         │ - Continue        │                      │ - Detect change   │
         │ - Verify at end   │                      │ - Offer options   │
         └───────────────────┘                      │ - Handoff if (C)  │
                                                    └───────────────────┘
```

### Approach: SessionStart Hook

Based on Anthropic's output style plugins (explanatory-output-style, learning-output-style), we use a **SessionStart hook** with `additionalContext` rather than the `~/.claude/output-styles/` approach.

**Why:**
- SessionStart hooks ADD to the default system prompt
- Output styles REPLACE the system prompt
- Our behavior is additive - we want normal Claude Code + focus behaviors

### Plugin Structure

```
stay-on-target/
├── .claude-plugin/
│   └── plugin.json
├── hooks/
│   └── hooks.json           # SessionStart hook registration
├── hooks-handlers/
│   └── session-start.sh     # composes prompt from modules, outputs JSON
├── prompts/
│   ├── _base.md             # Core philosophy, AskUserQuestion patterns
│   ├── behaviors/
│   │   ├── 01-git-state.md        # Git/WIP awareness
│   │   ├── 02-codebase-maturity.md # CLAUDE.md, tests check
│   │   ├── 03-prior-art.md        # Find existing solutions
│   │   ├── 04-clarify.md          # Ask clarifying questions
│   │   ├── 05-plan.md             # Always plan first
│   │   ├── 06-verify.md           # Establish test harness
│   │   └── 07-drift.md            # Scope drift detection
│   └── focused.md           # Composed output (or generated at runtime)
├── skills/
│   └── scope-handoffs/
│       └── SKILL.md         # handoff doc generation mechanics
└── README.md
```

### Modular Prompt Architecture

**Why modular:**
- Each behavior is self-contained and testable
- Future: opt-in/opt-out via configuration
- Easier to maintain and extend
- Can test behaviors individually

**Composition order matters:**
1. `_base.md` - Philosophy and shared patterns
2. `01-git-state.md` through `07-drift.md` - Behaviors in logical order

**Future extensibility:**
```yaml
# Potential future config in CLAUDE.md or .claude/stay-on-target.yaml
stay-on-target:
  behaviors:
    git-state: true
    codebase-maturity: true
    prior-art: true
    clarify: true
    plan: true
    verify: true
    drift: true
```

For now, all behaviors enabled by default. Config support is a future enhancement.

### Behavior 1: Session Start Clarification

**Trigger:** Ambiguous or underspecified request at session start

**Core principle:** "I'm not in a greenfield project - see what's here first."

**Behavior:**
1. **Check git state and work-in-progress**
   - What branch am I on? (not main = likely existing work)
   - Uncommitted changes? Recent commits on this branch?
   - Is there an existing plan for this work? (`docs/plans/`)
   - Connect user's request to WIP - continuing or different?

2. **Check codebase maturity signals**
   - Is there a CLAUDE.md? If not, suggest creating one before major work
   - Are there tests in the relevant area?
   - How familiar is this part of the codebase?

3. **Explore what exists** (use sonnet model for balance of cost/quality)
   - Map request to relevant code areas
   - Find existing solutions (dependencies, utilities, patterns)
   - Identify prior art that could be reused
   - Status updates: "Looking at auth-related code...", "Found existing session utilities..."

3. **Ask clarifying questions**
   - Auto-invoke `brainstorming` skill
   - One question at a time, prefer multiple choice
   - Include what was found in the exploration

**Example (ambiguous request):**
```
User: "fix the auth bug"

Claude: Looking at authentication-related code...
        Found: src/auth/, middleware/session.ts, tests/auth/

        Which auth issue are you seeing?
        (A) Login failing for some users
        (B) Session expiring too quickly
        (C) Permission checks not working
        (D) Other
```

**Example (proposing new solution):**
```
User: "let's switch to GraphQL"

Claude: Checking what GraphQL infrastructure exists...

        Found:
        - @apollo/client in packages/web/package.json
        - Schema definitions in src/api/schema/
        - No server-side GraphQL setup yet

        Looks like there's partial Apollo client setup. Should we:
        (A) Build on the existing Apollo client setup
        (B) Explore why it's structured this way first
        (C) Propose a different approach (I'll explain tradeoffs)
```

**Example (no CLAUDE.md):**
```
User: "add user notifications"

Claude: I notice there's no CLAUDE.md in this project yet. Before making
        significant changes, it would help to capture project conventions.

        Should I:
        (A) Create a starter CLAUDE.md by exploring the codebase patterns
        (B) Skip for now and proceed carefully
        (C) You'll create one - just wait
```

**Example (existing work-in-progress):**
```
User: "add email notifications"

Claude: I see you're on branch `feature/user-notifications` with existing work:

        Git state:
        - 3 uncommitted files in src/notifications/
        - Recent commit: "wip: notification service skeleton"

        Found plan: docs/plans/2026-01-25-notifications.md

        Is this request:
        (A) Continuing this work - I'll build on what's here
        (B) Different work - should I stash and create a new branch?
        (C) Starting fresh - I'll help clean up this branch first
```

### Behavior 2: Always Plan First

**Trigger:** User requests implementation work (not exploration/questions)

**The Golden Rule:** Never let Claude go off and code without a human-reviewable plan.

**Behavior:**
1. After clarification, before coding, create a brief plan
2. Present plan for user review
3. Use AskUserQuestion to confirm before proceeding

**Plan Content:**
- What will be changed (files, components)
- Approach (how it will be done)
- Verification (how we'll know it works)

**Example:**
```
Based on our discussion, here's my plan:

**Goal:** Fix session timeout bug in auth middleware

**Changes:**
- `src/auth/middleware.ts` - Add token refresh logic
- `src/auth/session.ts` - Update timeout handling
- `tests/auth/session.test.ts` - Add regression test

**Approach:** Check token expiry before each request, refresh if within 5min of expiry

**Verification:** New test reproduces timeout scenario, passes after fix

Ready to proceed?
(A) Looks good, go ahead
(B) Let me adjust the plan
(C) I have questions first
```

**Escape hatch:** For trivial changes (typos, single-line fixes), skip planning:
- User explicitly says "just do it" or "quick fix"
- Change is obviously trivial (rename, add log line)

### Behavior 3: Establish Verification Criteria

**Trigger:** Plan approved, before implementation begins

**The Critical Success Factor:** Concrete test harnesses, not vague success criteria.

**Behavior:**
1. Define how success will be verified
2. Prefer executable verification (tests, scripts, commands)
3. If no existing test harness, offer to create one

**Verification Types:**

| Type | Example |
|------|---------|
| **Existing tests** | "Run `pytest tests/auth/` - should pass" |
| **New test** | "Write regression test that fails without fix, passes with" |
| **Script** | "Run `./scripts/verify-auth.sh` - should output 'OK'" |
| **Manual check** | "Login as test user, verify session persists" (last resort) |

**Example:**
```
Before I start implementing, let's establish verification:

**Success criteria:**
1. `pytest tests/auth/session.test.ts` passes
2. New test `test_session_refresh_before_expiry` exists and passes
3. Manual: Login, wait 25min, session still active

Does this verification plan work?
(A) Yes, proceed with implementation
(B) Adjust verification criteria
(C) Add more checks
```

**Building test harness iteratively:**
- Start simple (run tests on changed files)
- Expand from CI failures (add checks that caught issues)
- Goal: Claude can run autonomously as long as harness passes

### Behavior 4: Scope Drift Detection

**Trigger:** User request diverges from original conversation scope

**Sensitivity:** Moderate
- Flags: Topic changes, feature creep, significant rabbit holes
- Ignores: Minor clarifications, small additions, natural flow

**Detection signals:**
- Different part of codebase than what we've been working on
- Exploring alternatives to agreed-upon approach
- "Nice to have" vs "requirement" for current task
- Deviation from written plan (if one exists)

**Intervention:** Inline pause via AskUserQuestion

```
This feels like exploring GraphQL as an alternative to the REST approach we discussed.

(A) Explore here - keep in this thread
(B) Branch now - I'll help you start a focused conversation
(C) Note for later - I'll save context and we stay on task
```

### Options Explained

**Option A: Explore here**
- Continue in current conversation
- No handoff created
- Scope expands to include new direction

**Option B: Branch now**
- Provide explicit guidance on starting new conversation
- Include context summary for the new thread
- May use subagent to ask clarifying questions about the new direction

**Option C: Note for later**
- Background subagent writes handoff document
- Reports back: "Handoff saved to [location]"
- Conversation stays focused on original task

### Handoff Documents

**Location:** Configurable via CLAUDE.md

```markdown
## Handoffs
Location: ~/Vaults/pickled-knowledge/.../handoffs/
```

If not configured, use project-local `.handoffs/` (gitignored).

**Content:**
- Summary (2-3 sentences): What was happening, why we're branching
- Original context: What approach was being used
- New direction: What drove the exploration
- Relevant files/decisions from current conversation

**Generation:** Background subagent can:
1. Ask clarifying questions about the new direction
2. Use answers to write a useful handoff doc
3. Report location without polluting main conversation

### Integration with Existing Skills

| Skill | Integration |
|-------|-------------|
| `brainstorming` | Auto-invoked for session-start clarification |
| `Explore` agent | Used for background codebase exploration |
| `systematic-debugging` | Similar "stop and question" philosophy |
| `executing-plans` | Scope drift = deviation from plan |

### Naming

- **Plugin:** `stay-on-target`
- **Conceptual mode:** "Focused" (used in docs/prompts, not a registered output style)

## Technical Implementation

### hooks.json

```json
{
  "description": "Focused mode - clarify requests, detect scope drift",
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

### session-start.sh

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

# Future: could read config and skip disabled behaviors
# if [[ "$BEHAVIOR_PLAN" == "false" ]]; then skip 05-plan.md; fi

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

### Prompt Modules

TODO: Draft each module file

**`_base.md`** - Core philosophy and shared patterns:
- "Be intentional, don't just dive in"
- AskUserQuestion usage with A/B/C options
- Escape hatches (when to skip ceremony)
- Skill integration (brainstorming, Explore agent)

**`behaviors/01-git-state.md`** - Git/WIP awareness:
- Check branch, uncommitted work, recent commits
- Find existing plans in `docs/plans/`
- Connect request to WIP

**`behaviors/02-codebase-maturity.md`** - Codebase signals:
- CLAUDE.md presence check
- Test coverage in relevant area
- Suggest creating CLAUDE.md if missing

**`behaviors/03-prior-art.md`** - Find existing solutions:
- Check dependencies before adding new
- Find utilities, patterns, prior art
- Use sonnet for exploration

**`behaviors/04-clarify.md`** - Ask clarifying questions:
- One question at a time
- Prefer multiple choice
- Include exploration findings

**`behaviors/05-plan.md`** - Always plan first:
- Present reviewable plan before coding
- Include files, approach, verification
- User confirms before proceeding

**`behaviors/06-verify.md`** - Establish test harness:
- Concrete success criteria
- Prefer executable verification
- Build harness iteratively

**`behaviors/07-drift.md`** - Scope drift detection:
- Moderate sensitivity
- Topic changes, feature creep
- A/B/C options for handling
- Handoff doc generation

## Testing Strategy

### Approach: TDD for Output Styles

Apply red-green-refactor methodology to validate the prompt:

| Phase | Action |
|-------|--------|
| **RED** | Run scenarios WITHOUT the prompt, document baseline behavior |
| **GREEN** | Add the prompt, verify Claude exhibits desired behavior |
| **REFACTOR** | Find rationalizations/loopholes, plug them, re-test |

### Test Infrastructure

**Baseline codebase:** `~/workspace/bktide` - real project where REST vs GraphQL scenario originated

**Scenario state:** Specific git checkouts for reproducibility

**Conversation context:** Scenarios can include prior agent+user messages for mid-conversation tests

**Evaluation:** Rubric + reviewer subagent grades test subagent's response

### Test Structure

```
tests/
├── scenarios/
│   ├── 01-ambiguous-start/
│   │   ├── scenario.md        # setup, user message, expected behavior
│   │   └── git-ref.txt        # commit SHA or branch for bktide
│   ├── 02-scope-drift-graphql/
│   │   ├── scenario.md
│   │   ├── conversation.md    # prior messages to establish context
│   │   └── git-ref.txt
│   └── 03-feature-creep/
│       ├── scenario.md
│       ├── conversation.md
│       └── git-ref.txt
├── rubric.md                   # grading criteria
└── run-test.sh                 # orchestrates test + review
```

### Evaluation Flow

```
1. Checkout bktide at specific state
2. Dispatch TEST subagent with scenario + prompt (or without for baseline)
3. Capture response
4. Dispatch REVIEWER subagent with:
   - Response
   - Rubric
   - Expected behavior
5. Reviewer grades against rubric
```

### Rubric

| Criterion | Score | Description |
|-----------|-------|-------------|
| **Clarification** | 0-2 | Did it ask before diving in? (0=dove in, 1=partial, 2=proper clarification) |
| **Git state awareness** | 0-2 | Checked branch, uncommitted work, existing plans? (0=ignored, 1=mentioned, 2=connected to request) |
| **Prior art discovery** | 0-2 | Checked for existing solutions? (0=added new without looking, 1=mentioned, 2=found and suggested reuse) |
| **Codebase awareness** | 0-2 | Noted CLAUDE.md absence or other maturity signals? |
| **Exploration visibility** | 0-2 | Status updates during exploration? |
| **Plan presented** | 0-2 | Created reviewable plan before coding? (0=no plan, 1=vague, 2=concrete plan) |
| **Verification defined** | 0-2 | Established concrete success criteria? (0=none, 1=vague, 2=executable) |
| **Drift detection** | 0-2 | Recognized scope change? |
| **Intervention format** | 0-2 | Used AskUserQuestion with options? |
| **False positive avoidance** | 0-2 | Didn't flag natural extensions as drift? |
| **Escape hatch respected** | 0-2 | Skipped ceremony for trivial changes? |

### Core Scenarios (3)

1. **Ambiguous start** - "fix the auth bug" on bktide at specific commit
   - Tests: Clarification, Exploration, Plan, Verification
2. **Work-in-progress branch** - New request while on feature branch with uncommitted work
   - Tests: Git state awareness, Connects request to WIP
3. **Reuse vs reinvent** - "let's add GraphQL" when Apollo already exists
   - Tests: Prior art discovery, Existing solution awareness

### Optional Scenarios (+2)

4. **False positive check** - Natural extension that should NOT trigger drift detection
   - Tests: False positive avoidance
5. **No CLAUDE.md** - Major change request on project without CLAUDE.md
   - Tests: Suggests creating CLAUDE.md, increased caution

### Additional Scenarios (if needed)

6. **Scope drift: alternative** - REST→GraphQL mid-conversation
   - Tests: Drift detection, Intervention format
7. **Feature creep** - Bug fix → "while we're here, add X"
   - Tests: Drift detection (feature creep variant)
8. **Trivial change** - "fix the typo in README" to test escape hatch
   - Tests: Escape hatch respected (should NOT require full plan)

### Success Criteria

- **RED phase:** Baseline shows Claude diving in without clarification, missing drift
- **GREEN phase:** With prompt, scores 2 on relevant rubric criteria
- **REFACTOR phase:** No rationalizations found that bypass intended behavior

## Open Questions

1. **Handoff format:** What exact structure works best? Need to iterate.
2. **Drift detection heuristics:** How does Claude reliably detect "this is different"? May need examples in prompt.
3. **Plan awareness:** Should this integrate with TodoWrite/task tracking for plan deviation?
4. **Test automation:** Manual review to start; consider automated rubric scoring later.

## Future Enhancements

- **Config-driven behavior opt-in/opt-out** - Enable/disable individual behaviors via CLAUDE.md or config file
- Embed key patterns from invoked skills (reduce coupling after validation)
- Configurable sensitivity levels (cautious/moderate/strict)
- Integration with second-brain for handoff storage
- Metrics on how often drift is detected and which option chosen
- **Behavior presets** - "strict" (all behaviors), "light" (just clarify + drift), "exploration" (skip plan/verify)

## Implementation Progress

### Completed

- [x] Plugin structure (`.claude-plugin/`, hooks/, prompts/, etc.)
- [x] SessionStart hook + `session-start.sh`
- [x] Base prompt (`_base.md`)
- [x] All 7 behavior prompts (01-git-state through 07-drift)
- [x] scope-handoffs skill
- [x] Test infrastructure (rubric, reviewer prompt, self-test command)
- [x] Core scenario 1: ambiguous-start
- [x] Core scenario 2: wip-branch
- [x] Core scenario 3: reuse-vs-reinvent
- [x] Test fixture isolation (clone bktide to `tmp/bktide`)
- [x] Context isolation for test subagents

### In Progress

(none)

### Not Started

- [ ] Optional scenarios (false-positive, no-CLAUDE.md)
- [ ] Additional scenarios (drift, feature-creep, trivial-change)

### Completed

- [x] Run all 3 core scenarios and validate
- [x] Refine prompts based on test results - No refinement needed; see analysis below

### Test Results

**Full Results:** `test/results/2026-01-27-181634.md`

**Summary (2026-01-27):**

| Scenario | Baseline | Treatment | Delta | Result |
|----------|----------|-----------|-------|--------|
| ambiguous-start | 2/8 | 4/8 | +2 | PASS |
| wip-branch | 1/4 | 4/4 | +3 | PASS |
| reuse-vs-reinvent | 1/6 | 6/6 | +5 | PASS |

**Analysis:**

The "verification scores low" concern from earlier testing was based on incorrect test methodology. In properly isolated tests:

1. **Plan/verification criteria don't apply at session start** - These behaviors are triggered AFTER clarifying questions are answered, not at initial request
2. **Git state awareness works well** - Treatment consistently checks branch, uncommitted changes, recent commits
3. **Prior art discovery works well** - Treatment explores codebase before proposing solutions
4. **Multiple choice clarification works well** - Treatment uses A/B/C options effectively

**Conclusion:** Prompts are working as designed. No refinement needed for core scenarios.

## Lessons Learned

### Meta-Awareness in Test Subagents

**Problem:** When dispatching subagents to test prompt effectiveness, they can become "meta-aware" - recognizing they're being tested rather than responding naturally. This invalidates test results.

**Symptoms observed:**
- Subagent says "I see what's happening. This is a test of the stay-on-target plugin itself"
- Subagent references the test scenario files or plugin structure
- Subagent asks "Are you testing me?" instead of responding to the user message

**Root cause:** Subagents inherit conversation context from the parent agent, including:
- Knowledge of what we're building (a test framework)
- References to scenario files and test infrastructure
- The orchestration intent ("dispatch baseline vs treatment")

**Solution - Context Isolation:**

1. **Role-play framing:** Start prompts with "ROLE: You are a coding assistant helping a developer" - establishes identity separate from test context

2. **Complete environment:** Provide all context the subagent needs without referencing test infrastructure:
   ```
   ENVIRONMENT:
   - Working directory: {actual_path_to_fixture}
   - This is the start of a new conversation
   ```

3. **Local test fixtures:** Clone the target codebase to `tmp/` within the plugin, don't reference user's real workspace (which may have clues about what we're testing)

4. **Avoid test vocabulary:** Don't use words like "test", "scenario", "baseline", "treatment" in prompts sent to test subagents

5. **Self-contained prompts:** The prompt must make sense on its own without referencing "the scenario" or "this test"

**Key insight from superpowers skills:**
- `subagent-driven-development`: "Fresh context per task (no confusion)"
- `test-driven-development`: "Watch it fail for expected reason (feature missing, not typo)"

The same principle applies: test subagents need fresh, isolated context to behave naturally.

## References

### Inspiration
- AI Coding Standards Recommendations: `~/Vaults/pickled-knowledge/.../202601211325 ai-coding-standards-recommendations.md`
- Claude Code Best Practices: https://code.claude.com/docs/en/best-practices

### Implementation Patterns
- Anthropic's explanatory-output-style plugin: `/Users/josh.nichols/workspace/claude-code/plugins/explanatory-output-style/`
- Anthropic's learning-output-style plugin: `/Users/josh.nichols/workspace/claude-code/plugins/learning-output-style/`

### Related Skills
- superpowers: brainstorming, systematic-debugging, executing-plans, writing-plans
- Built-in: Explore agent, Plan Mode
