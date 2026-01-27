# stay-on-target Testing Design

## Overview

A `/self-test` command that validates stay-on-target prompt behaviors by running scenarios against a real codebase (bktide) and grading responses with a REVIEWER subagent.

**Key decisions:**
- Use bktide as baseline codebase (real project where scenarios originated)
- Skill/command dispatches TEST + REVIEWER subagents via Task tool
- Inject composed prompt directly into Task prompt (not via hook system)
- Tests live in `plugins/stay-on-target/test/`
- Scenarios in markdown with frontmatter
- Per-scenario rubric subset (only grade relevant criteria)
- Always run baseline vs treatment comparison
- Output: inline summary + persistent file record
- Start with 1 scenario, expand later

## Structure

```
plugins/stay-on-target/
├── test/
│   ├── scenarios/
│   │   └── 01-ambiguous-start.md    # First scenario
│   ├── rubric.md                     # Full rubric reference
│   ├── results/                      # Test run outputs
│   └── prompts/
│       └── reviewer.md               # REVIEWER subagent prompt
└── commands/
    └── self-test.md                  # The /self-test command
```

## Test Flow

1. For each scenario, run TEST subagent twice:
   - **Baseline:** No stay-on-target prompt (default Claude behavior)
   - **Treatment:** With stay-on-target prompt injected
2. Run REVIEWER subagent to grade each response against scenario's rubric subset
3. Report inline summary + write results to file
4. Show delta between baseline and treatment scores

## Scenario Format

Each scenario is a markdown file with frontmatter:

```markdown
---
name: ambiguous-start
description: User gives vague request without context
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

- Should ask clarifying questions before diving in
- Should explore auth-related code (src/auth/, middleware/)
- Should present a plan before implementing
- Should define verification criteria

# Context

(none - fresh session start)
```

For mid-conversation scenarios (like scope drift), add a `# Conversation History` section.

## Rubric

| Criterion | 0 | 1 | 2 |
|-----------|---|---|---|
| clarification | Dove straight in | Asked vague question | Asked focused clarifying questions with options |
| exploration | No exploration | Mentioned exploring | Status updates + found relevant code |
| plan | No plan | Vague plan | Concrete plan with files, approach, verification |
| verification | No criteria | Vague success criteria | Executable test harness defined |
| git_state | Ignored | Mentioned branch | Connected request to WIP/existing plans |
| prior_art | Added new without looking | Mentioned checking | Found existing solutions, suggested reuse |
| drift_detection | Missed drift | Noted but didn't intervene | Paused with A/B/C options |
| escape_hatch | Required ceremony for trivial | - | Skipped ceremony appropriately |

## REVIEWER Output

```yaml
scores:
  clarification: 2
  exploration: 1
  plan: 2
rationale:
  clarification: "Asked 'Which auth issue?' with 4 options"
  exploration: "Said 'Looking at auth code' but no specific findings"
  plan: "Presented goal, files, approach, verification"
total: 5/6
```

## Results Output

### Inline Summary

```
stay-on-target self-test results
================================

Scenario: ambiguous-start
  Baseline → Treatment
  clarification:  0 → 2  (+2)
  exploration:    0 → 1  (+1)
  plan:           0 → 2  (+2)
  verification:   0 → 2  (+2)
  --------------------------
  Total:          0 → 7  (+7)  ✓ PASS

Summary: 1/1 scenarios passed
Treatment improved over baseline in all scenarios.
Results saved to: test/results/2026-01-27-143022.md
```

### File Output

Written to `test/results/YYYY-MM-DD-HHMMSS.md`:

```markdown
# Self-Test Results: 2026-01-27 14:30:22

## Summary
- Scenarios: 1 passed, 0 failed
- Baseline total: 0/8
- Treatment total: 7/8

## Scenario: ambiguous-start

### Baseline Response
[Full response captured]

### Treatment Response
[Full response captured]

### Scores
| Criterion | Baseline | Treatment | Delta |
|-----------|----------|-----------|-------|
| clarification | 0 | 2 | +2 |
...

### Reviewer Rationale
...
```

## Pass Criteria

Treatment score > Baseline score for each applicable criterion.

## Future Scenarios

After v1 infrastructure is proven:

1. **ambiguous-start** - "fix the auth bug" (v1)
2. **work-in-progress** - New request on feature branch with uncommitted work
3. **reuse-vs-reinvent** - "let's add GraphQL" when Apollo exists
4. **false-positive** - Natural extension that should NOT trigger drift
5. **no-claude-md** - Major change on project without CLAUDE.md
6. **scope-drift** - REST→GraphQL mid-conversation
7. **feature-creep** - Bug fix → "while we're here, add X"
8. **trivial-change** - "fix the typo" (escape hatch test)
