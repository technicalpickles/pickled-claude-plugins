---
name: park
description: Use when the user asks to park, hand off, wrap up or checkpoint the current session, or an automated idle prompt invokes a park
allowed-tools: Bash(scripts/get-session-id.sh)
---

# Park

Write one file a fresh session can resume from without reading this one. Park has three modes. Pick one, write that shape, do not mix.

## Modes

| Mode | Use when | Heading | Filename |
|------|----------|---------|----------|
| **Continuation** | Bouncing to a new session, work continues | `Parked:` | `YYYYMMDDHHMM [topic-slug].md` |
| **Close-out** | Work is done, capturing a record before walking away | `Wrapped:` | `YYYYMMDDHHMM [topic-slug]-wrapped.md` |
| **Idle checkpoint** | Automated park triggered by inactivity/cache-expiry, not a user request | `Checkpoint:` | `YYYYMMDDHHMM [topic-slug]-checkpoint.md` |

## Mode Detection

Pick one mode by checking these signals in order. Stop at the first one that resolves.

0. **Automated trigger.** If the invoking prompt explicitly identifies itself as an automated/idle-triggered park (e.g. names a watchdog, cron, or "idle-triggered" rather than a person asking) → idle checkpoint. Skip every other signal below. Automated callers run headless and cannot answer a question.
1. **Explicit user hint.**
   - "park, I'm done" / "wrap this up" / "park to close it out" / "park as record" → close-out
   - "park, switching sessions" / "park to continue" / "park, picking back up later" → continuation
2. **Terminal-state inference.** If all major next steps are done, no blockers remain, and the current state reads as terminal → close-out. If concrete unfinished next actions exist → continuation.
3. **Ambiguity fallback.** Use the AskUserQuestion tool with one A/B question:
   - Question: "Is this a close-out (work is done, archiving) or a continuation (planning to pick this up in a new session)?"
   - Options: "Close-out (record)" / "Continuation (handoff)"

Signal 3 requires an interactive caller. A headless or automated invocation must already have resolved at signal 0.

Pick once and commit. Do not switch modes mid-write.

## Before Writing

1. Resolve session ID:
   - **Session ID:** `${CLAUDE_SESSION_ID}`
   - Claude Code fills in the value above when it loads this skill. If it is a UUID, use it.
   - **Fallback:** If the value above is not a UUID (another harness left it unfilled), run [scripts/get-session-id.sh](scripts/get-session-id.sh) via Bash. If that prints nothing, use `unknown`.
2. Gather the git branch, the absolute worktree path, and the identifiers the next session will check: PR numbers, task UUIDs, commit SHAs.
3. Resolve output location, in order:
   1. Injected context has a `Park vault:` line and `<vault>/CLAUDE.md` has a `## Parking` section with a `Location:` → that folder, relative to the vault. The section supplies only the location; filenames follow this skill.
   2. Otherwise `.parkinglot/` in project root (verify it is gitignored). This also covers a vault with no `## Parking` section.
4. Get the timestamp with `date +%Y%m%d%H%M`. Every filename starts with it, then a single space.
5. Resolve the file's **absolute path**, whichever location it lands in. Every place this skill writes `[path]` takes that absolute path, because a relative path only resolves from one directory and a resumed session often starts elsewhere.

## Continuation Template

~~~markdown
# Parked: [Topic]

**Parked:** [Date/time]
**Session:** [session ID]
**Branch:** [branch-name]
**Worktree:** [absolute path, if applicable]

## Resume Prompt

```
unpark [path]

[Directives for the next session, at most three sentences. Omit when there are none.]
```

## Current State
- [One checkable fact per bullet, present tense]

## Key Decisions
- [Decision + why]

## Relevant Files
- path/to/file.ts (new|modified)

## Next Steps
1. [Concrete next action]
2. [Concrete next action]

## Open Questions
- [Question, and the step it blocks]
~~~

What each section holds:

- **Resume Prompt:** the `unpark` line, then directives: how the next session behaves, which skill or playbook it starts with, who is at the keyboard and what they want. The sections below carry state and actions, so the prompt carries neither. A rule that `CLAUDE.md` or a rules file already loads is not a directive. With no directives, the prompt is the `unpark` line alone.
- **Current State:** facts the next session can verify, each naming its identifier: the branch head or the uncommitted files, a PR number, a task UUID (never an integer task id, which gets reused), the test result. Unpark checks these against reality.
- **Key Decisions:** choices the diff and git history cannot show, each with its reason.
- **Relevant Files:** files the next session will change or must reread, marked `new` or `modified`. A file that was only read is not listed.
- **Next Steps:** the one place for actions, in the order to do them. The first is what the next session does first.
- **Open Questions:** only questions that block a step. Name the step. Omit the section when there are none.

**Name the skill, not the raw command, for steps that have a skill.** The resuming session tends to run whatever literal command the handoff spells out, and that skips the skill that would have handled it properly. So when a next step opens, edits, or comments on a PR, write "open the PR via the `git:pull-request` skill", not `gh pr create --title ... --body ...`. The same goes for commits (`git:commit`) and working through review feedback (`git:pull-feedback`). Keep the step's specifics (branch, what the PR body must cover, draft vs ready). Do not hand over a copy-paste command that routes around the skill.

**Session ID is load-bearing.** Unpark takes its first 8 characters to find this session's devlog. Never drop the line.

## Close-out Template

Use when the work is done and the user is walking away. There may be open threads, but no baton-pass.

~~~markdown
# Wrapped: [Topic]

**Wrapped:** [Date/time]
**Session:** [session ID]
**Branch:** [branch-name]
**Worktree:** [absolute path, if applicable]

## Outcome
[What got done. Past tense. Reference commits where applicable.]

## Key Decisions
- [Decision + why]

## Relevant Files
- path/to/file.ts (new|modified)

## Open Threads
[Optional. Things noticed but not done. One line each.
List follow-up candidates; don't file them in a tracker.]
~~~

Close-out has no Resume Prompt and no Next Steps. If you find yourself wanting to write either, the work is probably a continuation: re-check the mode.

## Idle Checkpoint Template

Written when a watchdog parks a session near its prompt-cache expiry, not when a person asked. Same shape and section rules as the continuation template, with three changes:

- Heading `# Checkpoint: [Topic]`.
- `**Checkpointed:**` replaces `**Parked:**`.
- A `**Trigger:** automated (idle)` line after `**Worktree:**`.

The labels tell a later `park` call in this same session what already happened here.

## After Writing

Close with the path and the resume line, each alone in a fenced block so it copies cleanly. Use the absolute path, with no blockquote and no quotes.

Continuation:

~~~
Parked to:

```
[path]
```

Resume in a new session:

```
unpark [path]
```
~~~

Close-out:

~~~
Wrapped to:

```
[path]
```

This is a close-out record. To start fresh work that builds on it, reference the file in your next session.
~~~

Idle checkpoint:

~~~
Checkpointed (automated, this session went idle) to:

```
[path]
```

If you're still working here, ignore this. To resume elsewhere:

```
unpark [path]
```
~~~
