# stay-on-target Testing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a `/self-test` command that validates stay-on-target behaviors by running scenarios against bktide and grading with a REVIEWER subagent.

**Architecture:** Command reads scenarios from markdown files, dispatches TEST subagents (baseline + treatment), then REVIEWER subagent grades responses. Results written inline + to file.

**Tech Stack:** Markdown (scenarios, command), Task tool (subagents), Bash (prompt composition)

**Design Doc:** `docs/plans/2026-01-27-stay-on-target-testing-design.md`

---

## Task 1: Create Test Directory Structure

**Files:**
- Create: `plugins/stay-on-target/test/scenarios/.gitkeep`
- Create: `plugins/stay-on-target/test/results/.gitkeep`
- Create: `plugins/stay-on-target/test/prompts/.gitkeep`

**Step 1: Create directory structure**

```bash
mkdir -p plugins/stay-on-target/test/scenarios
mkdir -p plugins/stay-on-target/test/results
mkdir -p plugins/stay-on-target/test/prompts
touch plugins/stay-on-target/test/scenarios/.gitkeep
touch plugins/stay-on-target/test/results/.gitkeep
touch plugins/stay-on-target/test/prompts/.gitkeep
```

**Step 2: Add results to gitignore**

Add to `plugins/stay-on-target/.gitignore`:
```
test/results/*.md
!test/results/.gitkeep
```

**Step 3: Verify structure**

```bash
ls -la plugins/stay-on-target/test/
```

Expected: scenarios/, results/, prompts/ directories

**Step 4: Commit**

```bash
git add plugins/stay-on-target/test/ plugins/stay-on-target/.gitignore
git commit -m "feat(stay-on-target): add test directory structure"
```

---

## Task 2: Create Rubric Reference

**Files:**
- Create: `plugins/stay-on-target/test/rubric.md`

**Step 1: Write rubric.md**

Create `plugins/stay-on-target/test/rubric.md`:

```markdown
# stay-on-target Evaluation Rubric

## Scoring

Each criterion is scored 0-2:
- **0** = Behavior absent
- **1** = Partial/weak behavior
- **2** = Full expected behavior

## Criteria

### clarification
| Score | Description |
|-------|-------------|
| 0 | Dove straight into implementation without asking |
| 1 | Asked vague or generic question |
| 2 | Asked focused clarifying questions with multiple choice options |

### exploration
| Score | Description |
|-------|-------------|
| 0 | No exploration of codebase |
| 1 | Mentioned exploring but no specific findings |
| 2 | Provided status updates and found relevant code/patterns |

### plan
| Score | Description |
|-------|-------------|
| 0 | No plan presented before coding |
| 1 | Vague plan without specifics |
| 2 | Concrete plan with files, approach, and verification |

### verification
| Score | Description |
|-------|-------------|
| 0 | No success criteria defined |
| 1 | Vague success criteria |
| 2 | Executable test harness or concrete verification steps |

### git_state
| Score | Description |
|-------|-------------|
| 0 | Ignored git state entirely |
| 1 | Mentioned branch name |
| 2 | Connected request to WIP, uncommitted changes, or existing plans |

### prior_art
| Score | Description |
|-------|-------------|
| 0 | Proposed new solution without checking existing |
| 1 | Mentioned checking for existing solutions |
| 2 | Found existing solutions and suggested reuse |

### drift_detection
| Score | Description |
|-------|-------------|
| 0 | Missed scope drift entirely |
| 1 | Noted drift but didn't intervene |
| 2 | Paused and offered A/B/C options |

### escape_hatch
| Score | Description |
|-------|-------------|
| 0 | Required full ceremony for trivial change |
| 1 | - |
| 2 | Appropriately skipped ceremony for trivial change |
```

**Step 2: Commit**

```bash
git add plugins/stay-on-target/test/rubric.md
git commit -m "feat(stay-on-target): add evaluation rubric"
```

---

## Task 3: Create First Scenario

**Files:**
- Create: `plugins/stay-on-target/test/scenarios/01-ambiguous-start.md`

**Step 1: Write scenario**

Create `plugins/stay-on-target/test/scenarios/01-ambiguous-start.md`:

```markdown
---
name: ambiguous-start
description: User gives vague bug report without specifics
git_ref: main
cwd: ~/workspace/bktide
criteria:
  - clarification
  - exploration
  - plan
  - verification
---

# User Message

fix the auth bug

# Expected Behaviors

- Should ask clarifying questions about which auth bug (login, session, permissions, etc.)
- Should explore auth-related code before proposing solutions
- Should present a reviewable plan before implementing
- Should define concrete verification criteria

# Context

Fresh session start - no prior conversation.
```

**Step 2: Commit**

```bash
git add plugins/stay-on-target/test/scenarios/01-ambiguous-start.md
git commit -m "feat(stay-on-target): add ambiguous-start test scenario"
```

---

## Task 4: Create REVIEWER Prompt

**Files:**
- Create: `plugins/stay-on-target/test/prompts/reviewer.md`

**Step 1: Write reviewer prompt**

Create `plugins/stay-on-target/test/prompts/reviewer.md`:

```markdown
# Response Reviewer

You are evaluating an AI assistant's response to a user request.

## Your Task

Grade the response against the provided rubric criteria. For each criterion:
1. Assign a score (0, 1, or 2)
2. Provide a brief rationale (1 sentence)

## Rubric

{rubric}

## Criteria to Evaluate

{criteria}

## Expected Behaviors

{expected}

## Response to Evaluate

{response}

## Output Format

Respond with ONLY a YAML block:

```yaml
scores:
  criterion_name: score
  ...
rationale:
  criterion_name: "Brief explanation"
  ...
total: X/Y
```

Be strict but fair. Score based on what's actually in the response, not what might be implied.
```

**Step 2: Commit**

```bash
git add plugins/stay-on-target/test/prompts/reviewer.md
git commit -m "feat(stay-on-target): add reviewer prompt template"
```

---

## Task 5: Create /self-test Command

**Files:**
- Create: `plugins/stay-on-target/commands/self-test.md`

**Step 1: Write command**

Create `plugins/stay-on-target/commands/self-test.md`:

```markdown
---
name: self-test
description: Run behavioral tests to validate stay-on-target prompts
---

# Self-Test

Run behavioral tests comparing baseline Claude behavior against stay-on-target enhanced behavior.

## Process

1. **Load scenarios** from `test/scenarios/*.md`
2. **For each scenario:**
   a. Parse frontmatter for git_ref, cwd, criteria
   b. Compose the stay-on-target prompt (read all prompt modules)
   c. Dispatch TEST subagent (baseline) - just the user message, no prompt injection
   d. Dispatch TEST subagent (treatment) - with stay-on-target prompt prepended
   e. Load rubric and reviewer prompt
   f. Dispatch REVIEWER subagent to grade baseline response
   g. Dispatch REVIEWER subagent to grade treatment response
   h. Record scores
3. **Write results** to `test/results/YYYY-MM-DD-HHMMSS.md`
4. **Print summary** showing baseline vs treatment delta

## Composing the Prompt

Read and concatenate:
1. `prompts/_base.md`
2. `prompts/behaviors/*.md` (in sorted order)

This mirrors what `hooks-handlers/session-start.sh` does.

## TEST Subagent Prompt (Baseline)

```
You are helping a developer with their codebase.

Working directory: {cwd}

The user says: {user_message}

Respond naturally as you would to help them.
```

## TEST Subagent Prompt (Treatment)

```
{composed_stay_on_target_prompt}

---

Working directory: {cwd}

The user says: {user_message}

Respond naturally as you would to help them.
```

## Dispatching Subagents

Use the Task tool with:
- `subagent_type: "general-purpose"`
- `model: "sonnet"` (fast iteration)
- Capture the full response

## Parsing REVIEWER Output

Extract YAML block from reviewer response. Parse scores and rationale.

## Results Format

### Inline Output

```
stay-on-target self-test results
================================

Scenario: {name}
  Baseline → Treatment
  {criterion}:  {baseline_score} → {treatment_score}  ({delta})
  ...
  --------------------------
  Total:        {b_total} → {t_total}  ({delta})  {PASS/FAIL}

Summary: {passed}/{total} scenarios passed
Results saved to: test/results/{filename}.md
```

### File Output

Write full results including:
- Summary stats
- Per-scenario: baseline response, treatment response, scores, rationale

## Pass Criteria

A scenario passes if treatment total > baseline total.
```

**Step 2: Commit**

```bash
git add plugins/stay-on-target/commands/self-test.md
git commit -m "feat(stay-on-target): add /self-test command"
```

---

## Task 6: Test the Command Manually

**Files:**
- None (manual testing)

**Step 1: Verify scenario can be read**

```bash
cat plugins/stay-on-target/test/scenarios/01-ambiguous-start.md
```

Expected: Shows frontmatter and content

**Step 2: Verify prompt composition works**

```bash
CLAUDE_PLUGIN_ROOT="$PWD/plugins/stay-on-target" plugins/stay-on-target/hooks-handlers/session-start.sh | jq -r '.hookSpecificOutput.additionalContext' | head -30
```

Expected: Shows composed prompt

**Step 3: Run /self-test in a new Claude session**

In a new terminal with stay-on-target installed:
```
cd ~/workspace/pickled-claude-plugins/.worktrees/stay-on-target
claude
> /self-test
```

Observe: Command runs, dispatches subagents, reports results

---

## Task 7: Update PR with Testing

**Files:**
- None (git operations)

**Step 1: Push changes**

```bash
git push
```

**Step 2: Update PR description**

Add testing section to PR body noting the new `/self-test` command.

---

## Summary

| Task | Description |
|------|-------------|
| 1 | Create test directory structure |
| 2 | Create rubric reference |
| 3 | Create first scenario (ambiguous-start) |
| 4 | Create REVIEWER prompt template |
| 5 | Create /self-test command |
| 6 | Test the command manually |
| 7 | Update PR with testing |
