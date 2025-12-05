# Design: /reflect Slash Command

**Date:** 2025-12-05
**Location:** `plugins/dev-tools/commands/reflect.md`
**Purpose:** Capture learnings from the current conversation through guided reflection

## Overview

A slash command that helps capture retrospectives of Claude conversations. The agent analyzes the current session, asks the user 3-4 focused questions, then generates a structured reflection document.

### Why This Exists

- Conversations contain valuable learnings that get lost
- Failed attempts and corrections reveal gaps in skills/workflows
- User perspective adds context the agent can't infer
- Structured capture enables pattern recognition across sessions

## Flow

1. User invokes `/reflect`
2. Agent analyzes current conversation (automatic)
3. Agent asks 3-4 questions (interactive)
4. Agent generates retrospective document
5. Saves to `docs/retrospectives/YYYY-MM-DD-<topic>.md` in current project

## Inline Notes with @reflect

Users can tag observations during the conversation:

```
@reflect this approach feels heavy for such a simple task
@reflect interesting that it chose grep over glob here
@reflect the skill helped catch this early
```

These are proactive observations (not corrections) that get collected when `/reflect` runs. They appear in a dedicated section in the output.

**Distinction:**
- **Corrections** — Reactive, user had to intervene to change direction
- **@reflect notes** — Proactive observations, no intervention required

## What the Agent Analyzes

**Automatically captured:**
- Failed attempts — What was tried and didn't work, how resolved
- Corrections made — Where user feedback changed direction
- Skills activated — Which skills were invoked
- Key decisions — Significant choices about approach
- Hook interventions — Tool calls blocked/redirected
- @reflect notes — User observations tagged during session

## User Prompts

Four focused questions to capture user perspective:

### Q1: Outcome
"Did we accomplish what you set out to do? What's the status?"
- Options: Fully complete / Partially complete / Blocked / Abandoned

### Q2: Approach
"How did the approach feel? Any decisions that seemed off?"
- Open-ended

### Q3: Skills (only if skills were used)
"Did any skills help or get in the way?"
- Options: Helped / Got in the way / Mixed / No opinion

### Q4: Friction
"Where did you have to intervene or correct course?"
- Open-ended

## Output Format

```markdown
# Reflection: [Brief Topic Description]

**Date:** YYYY-MM-DD
**Outcome:** [Fully complete | Partially complete | Blocked | Abandoned]
**Skills Used:** skill-a, skill-b (or "None")

## Summary

[2-3 sentences: what was the task, what happened, what was learned]

## What Happened

### Key Decisions
- [Decision 1 and reasoning]
- [Decision 2 and reasoning]

### Failed Attempts
- [What failed] → [How it was resolved]

### Corrections Made
- [User correction] → [Impact on direction]

## Notes Captured

[Any @reflect observations from during the session, omit section if none]

## User Feedback

**Approach:** [Your answer to Q2]

**Skills:** [Your answer to Q3 + any elaboration]

**Friction points:** [Your answer to Q4]

## Lessons Learned

### For Agent Workflows
- [Lesson 1]
- [Lesson 2]

### For Skills
- [Any gaps identified or improvements needed]

## Action Items

- [ ] [Concrete follow-up if any]
```

**Output location:** `docs/retrospectives/YYYY-MM-DD-<topic>.md` in current project

## Implementation Notes

### Slash Command Structure

The command file (`plugins/dev-tools/commands/reflect.md`) will contain:
- Frontmatter with description
- Instructions for the agent to:
  1. Reflect on the conversation so far
  2. Identify failed attempts, corrections, skills used, key decisions
  3. Ask the 4 questions using AskUserQuestion
  4. Generate the retrospective in the specified format
  5. Save to the appropriate location

### Edge Cases

- **No failures/corrections:** Still valuable to capture decisions and outcome
- **No skills used:** Skip Q3, note "None" in output
- **Very short conversation:** May not have much to capture, that's fine
- **docs/retrospectives/ doesn't exist:** Create it

### Not in Scope

- Analyzing exported conversations (future enhancement)
- Aggregating insights across multiple retrospectives
- Automatic skill improvement suggestions
