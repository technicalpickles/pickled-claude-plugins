---
description: Capture learnings from the current conversation through guided reflection
---

# Reflect on This Conversation

Help capture a retrospective of this conversation. You'll analyze what happened, ask the user a few questions, then generate a structured reflection document.

## Step 1: Analyze the Conversation

Review the conversation so far and identify:

### Failed Attempts
What was tried and didn't work? How was each failure resolved?
- Look for error messages, retries, or approaches that were abandoned
- Note what the resolution was (user correction, different approach, etc.)

### Corrections Made
Where did the user provide feedback that changed direction?
- Explicit corrections ("no, do it this way")
- Redirections ("let's try something else")
- Clarifications that revealed a misunderstanding

### Skills Activated
Which skills were invoked during this conversation?
- Look for Skill() tool calls
- Look for announcements like "I'm using the X skill"
- Note the skill names

### Key Decisions
What significant choices were made about approach, tools, or architecture?
- Why was each decision made?
- Were alternatives considered?

### Hook Interventions
Were any tool calls blocked or redirected by hooks?
- What was blocked?
- What was the workaround?

### @reflect Notes
Scan user messages for `@reflect` tags — these are observations the user wanted captured.
- Collect all `@reflect <note>` entries
- These are proactive observations, not corrections

## Step 2: Ask the User

Ask these questions to get the user's perspective. Use the AskUserQuestion tool with all questions at once:

**Q1 - Outcome:** "Did we accomplish what you set out to do?"
- Options: Fully complete / Partially complete / Blocked / Abandoned

**Q2 - Approach:** "How did the approach feel? Any decisions that seemed off?"
- Open-ended text

**Q3 - Skills:** (Only if skills were used) "Did any skills help or get in the way?"
- Options: Helped / Got in the way / Mixed / No opinion

**Q4 - Friction:** "Where did you have to intervene or correct course?"
- Open-ended text

## Step 3: Generate the Retrospective

Create a markdown document with this structure:

```markdown
# Reflection: [Brief Topic Description]

**Date:** YYYY-MM-DD
**Outcome:** [User's answer to Q1]
**Skills Used:** [comma-separated list, or "None"]

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

[List any @reflect observations from during the session. Omit this section if none.]

## User Feedback

**Approach:** [User's answer to Q2]

**Skills:** [User's answer to Q3, if applicable]

**Friction points:** [User's answer to Q4]

## Lessons Learned

### For Agent Workflows
- [Lesson 1]
- [Lesson 2]

### For Skills
- [Any gaps identified or improvements needed. Omit if no skills were used or no lessons apply.]

## Action Items

- [ ] [Concrete follow-up if any. Omit section if none.]
```

## Step 4: Save the Document

1. Determine a brief topic slug from the conversation (e.g., "tool-routing-multiline", "auth-refactor")
2. Create the directory if needed: `docs/retrospectives/`
3. Save to: `docs/retrospectives/YYYY-MM-DD-<topic>.md`
4. Tell the user where it was saved

## Guidelines

- Keep the summary concise (2-3 sentences)
- Be specific about what failed and why
- Capture the user's perspective accurately
- If sections have no content (no failed attempts, no corrections), you can note "None" or omit subsections
- The retrospective should be useful for future reference, not exhaustive documentation
