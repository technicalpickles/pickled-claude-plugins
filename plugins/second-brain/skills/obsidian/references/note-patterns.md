# Note Patterns

Common note templates for different types of content. Use these when vault doesn't have its own templates.

## Person Note

For tracking people - colleagues, contacts, authors, etc.

```markdown
---
tags: #person
---

# [Full Name]

## Context

How you know them, their role, team, etc.

## Interactions

### YYYY-MM-DD - [Topic]

Notes from interaction.

## Related

- [[Related Note]]
```

**Location:** `Areas/People/` or similar
**Filename:** `Full Name.md` (no zettelkasten prefix for people)

---

## Meeting Note

For capturing meeting discussions and outcomes.

```markdown
---
tags: #meeting
---

# [Meeting Title]

**Date:** YYYY-MM-DD
**Participants:** Names

## Summary

1-3 bullet executive summary.

## Discussion

### Topic 1

Notes...

### Topic 2

Notes...

## Action Items

- [ ] Action item (@owner)

## Decisions

- Decision made

## Related

- [[Related Note]]
```

**Location:** Varies - project folder, area folder, or daily note
**Filename:** `YYYYMMDDHHMM meeting-title.md`

---

## Idea/Concept Note

For capturing ideas worth developing.

```markdown
---
tags: #idea
---

# [Idea Title]

## Origin

Where this idea came from - conversation, reading, observation.

## The Idea

Core concept explained.

## Why It Matters

Potential value or application.

## Open Questions

- Question to explore
- Another question

## Related

- [[Related Note]]
```

**Location:** `Inbox/` initially, then move to appropriate Area/Resource
**Filename:** `YYYYMMDDHHMM idea-title.md`

---

## Investigation Note

For debugging, research, or analysis work.

```markdown
---
tags: #investigation
---

# [Investigation Title]

**Status:** Active | Resolved | Blocked
**Date:** YYYY-MM-DD

## Problem

What we're investigating.

## Hypotheses

1. Hypothesis one
2. Hypothesis two

## Evidence

### For Hypothesis 1

- Evidence point
- Link to dashboard/log

### Against Hypothesis 1

- Counter-evidence

## Findings

What we learned.

## Action Items

- [ ] Next step

## Related

- [[Related Note]]
```

**Location:** Project folder or `Areas/[domain]/`
**Filename:** `YYYYMMDDHHMM investigation-title.md`

---

## Project Note

For tracking a project with deliverables.

```markdown
---
tags: #project
---

# [Project Name]

**Status:** Planning | Active | On Hold | Complete
**Target:** YYYY-MM-DD (if applicable)

## Goal

What success looks like.

## Context

Why this project exists.

## Plan

1. Step one
2. Step two

## Progress

### YYYY-MM-DD

Update on progress.

## Related

- [[Related Note]]
```

**Location:** `Projects/[category]/`
**Filename:** `YYYYMMDDHHMM project-name.md` or just `project-name.md` for long-running projects

---

## Daily Note

See vault's `Fleeting/CLAUDE.md` or use this default:

```markdown
---
tags: #daily
---

## Action Items

- [ ] Task

## Notes

### Topic

Notes here.

## Extracted Notes

- [[YYYYMMDDHHMM Note]] - description

## Log

-
```

**Location:** `Fleeting/` or `Daily/`
**Filename:** `YYYY-MM-DD.md`

---

## Insight Note (Brain Capture)

For capturing insights from conversations, debugging sessions, or realizations.

```markdown
---
captured: {ISO timestamp}
source: claude-conversation
repo: {repo name or "none"}
branch: {branch name or "none"}
commit: {short commit hash or "none"}
---

# {Insight Title}

{The insight, cleaned up and clearly written. 1-3 paragraphs.}

## Context

Captured while {brief description of what you were working on/discussing}.

---
*Captured via /second-brain:insight*
```

**Location:** `Inbox/` initially, then route to appropriate Area/Resource
**Filename:** `YYYYMMDDHHMM insight-title.md`

**Provenance fields:**
- `captured` - ISO timestamp when captured
- `source` - Where it came from (claude-conversation, reading, etc.)
- `repo`, `branch`, `commit` - Git context if captured during coding

---

## Quick Reference: When to Use What

| Content Type | Pattern | Location |
|--------------|---------|----------|
| New contact | Person | Areas/People/ |
| Work meeting | Meeting | Project or Area folder |
| Random idea | Idea | Inbox/ → later organize |
| Conversation insight | Insight | Inbox/ → route after |
| Bug/issue | Investigation | Project folder |
| New initiative | Project | Projects/ |
| Daily capture | Daily | Fleeting/ |
