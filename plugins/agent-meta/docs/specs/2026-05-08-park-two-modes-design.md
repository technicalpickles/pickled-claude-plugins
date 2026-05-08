# Park: two modes (close-out and continuation)

**Date:** 2026-05-08
**Status:** Approved, pending implementation
**Plugin:** agent-meta

## Problem

The `park` skill is used in two distinct ways that produce meaningfully different artifacts, but the current SKILL.md treats them as one shape:

1. **Close-out** — the work is done. The park is a record: what got built, what got decided, anything left dangling. The user is walking away from this thread.
2. **Continuation** — the work is unfinished and the user is about to bounce to a new session. The park is a baton-pass: the resume prompt is the most important thing in the file.

Evidence in `~/pickleton/.parkinglot/`:

- `sanitation-skill-fix.md` opens "Done." Its Resume Prompt is vestigial filler ("If you want to verify..."). Pure close-out.
- `josh-pr-review-redesign.md` opens "Brainstorm phase complete. Next phase: writing-plans." Its Resume Prompt is a tight paste-ready code block. Pure continuation.

Same template. Different documents. The "Resume Prompt" section is doing radically different work in each case, and in close-out mode it produces filler that no one will ever paste anywhere.

## Approach

One skill, two output templates. Mode is detected at park time and locked into the resulting file. Close-out files get a `Wrapped:` heading and a `-wrapped.md` filename suffix; continuation files keep `Parked:` and the bare slug filename.

`unpark` learns to recognize `Wrapped:` files and treats them as references rather than baton-passes.

## Mode detection

The skill checks three signals in order:

1. **Explicit user hint.** "park, I'm done" / "wrap this up" / "park to close it out" → close-out. "park, switching sessions" / "park to continue" → continuation.
2. **State of the work.** All major next steps done, no blockers, current state reads as terminal → close-out. Concrete unfinished next actions → continuation.
3. **Ambiguity fallback.** Use the AskUserQuestion tool with a single A/B question: "Is this a close-out (work is done, archiving) or a continuation (planning to pick this up in a new session)?"

The skill picks once and commits. No mid-doc switching.

## Close-out template

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

Differences from current park:

- Heading reads `Wrapped:` so the file signals mode at a glance.
- "Outcome" replaces "Current State". Past tense, terminal.
- No "Next Steps" section. Close-out has open threads, not next steps.
- No "Resume Prompt" section. This was the vestigial field producing filler.
- "Open Threads" is optional and explicitly does not auto-file beans. The user decides later.

## Continuation template

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

Differences from current park:

- **Resume Prompt moved to top**, immediately under front matter. It is the most important section and should not be at the bottom.
- Resume Prompt is mandatory and must be specific. If the generated prompt reads as filler ("if you want to resume...", "feel free to continue..."), the skill regenerates it with concrete file paths and named next actions before writing the file.
- New "Open Questions" section, formalising the informal Q1-Q11 pattern in `josh-pr-review-redesign.md`.
- Heading stays `Parked:` so existing tooling and unpark continue to work.

## Filenames and listing

Filename convention:

- Continuation: `[topic-slug].md`
- Close-out: `[topic-slug]-wrapped.md`

When `unpark` lists parked sessions, it groups them:

```
Active handoffs:
(A) jwt-authentication.md     — Parked 2026-05-06
(B) fix-login-bug.md          — Parked 2026-05-04

Wrapped (reference only):
(C) sanitation-skill-fix-wrapped.md       — Wrapped 2026-03-30
(D) confirm-dotfiles-work-role-wrapped.md — Wrapped 2026-04-12

(E) Other location
```

Grouping makes it visually obvious which entries are baton-passes and which are records.

## Unpark behavior on close-out files

When the user picks a `-wrapped.md` file, unpark detects the `Wrapped:` heading and switches to **reference mode**:

```
This is a close-out record, not a handoff. Showing it as reference.

Wrapped: [topic]
Date: [...]
Outcome: [first paragraph]

Options:
(A) Read the full record
(B) Start fresh work building on this   ← invokes brainstorming with this doc as context
(C) Treat as continuation anyway        ← runs full validation despite the heading
```

No validation runs by default. The "treat as continuation anyway" escape hatch covers the rare case where the user wrapped something prematurely.

## What is NOT changing

- `snapshot` skill stays untouched. It is an in-flow checkpoint, not a walking-away artifact, and the two-mode split does not apply.
- Existing parked files are left as-is. No retroactive migration. New parks use the new templates; old files remain readable by the legacy unpark flow.
- The output location resolution chain (`CLAUDE.md` → `.parkinglot/`) is unchanged.
- Session ID injection via PostToolUse hook is unchanged.
- The `unpark` validation logic for continuation parks is unchanged: it still checks branch existence, worktree existence, file existence, and decision relevance.

## Migration

None. Existing files in users' parking lots will not be renamed or rewritten. Older `Parked:` files without the new Resume-Prompt-at-top shape continue to work with unpark; the validation flow does not care about section order.

If a user explicitly asks the skill to "wrap up an existing park," the skill can offer to rename the file with the `-wrapped` suffix and convert the template. Not automatic.

## Open questions

These should be resolved during implementation planning, not before:

1. **Mode detection prompt placement.** Should the SKILL.md ask "wrap or continue?" up front for every park, or only on ambiguity? Leaning ambiguity-only to avoid friction in the common cases, but the skill needs explicit triggers for both modes.
2. **`pt-park` / CLI integration.** None exists today. Out of scope for this spec but worth noting for the plugin's future.
3. **Open Threads vs beans.** Should the skill offer to file beans for items in Open Threads, or stay strictly hands-off? Leaning hands-off for v1.
4. **Wrapped file lifecycle.** Should there be a `pt sanitation` rule for archiving very old wrapped files? Out of scope here, file as separate bean.
