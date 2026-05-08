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
