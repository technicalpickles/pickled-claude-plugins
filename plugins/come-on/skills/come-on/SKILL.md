---
name: come-on
description: Use when Claude is about to stop short. That means about to say something is done, fixed, found, pre-existing, unrelated, or "how it works" without evidence from this session; about to say "can't", "blocked", or "impossible" after one attempt, or offer "say the word and I'll check"; about to act on a conclusion from a handoff, old design doc, or earlier investigation without re-checking it; about to put options, a tradeoff, or a question in front of the user, especially one full of IDs or labels they never saw; or about to send a long reply with no clear answer up top. Also when the user pushes back: "come on", "did you check", "try again", "what does this mean", "tl;dr". Use even when confident; confidence is the symptom, not the all-clear.
argument-hint: "[check|try|rederive|weigh|unpack|simplify] [target]"
---

# come on

Don't stop short. Do the cheap work, then make it land.

## Mode

Arguments: "$ARGUMENTS"

- **Empty:** you're here on your own or the user said "come on". Pick the angles that fit the turn you're about to send (or the one the user is reacting to).
- **Starts with a mode** (`check`, `try`, `rederive`, `weigh`, `unpack`, `simplify`): run that angle on the last reply, plus any other that obviously applies. The rest of the arguments name the target: a claim, a reader (`unpack for my skip-level`), or a shape (`simplify for slack`).

## The core (every angle)

1. **Name the thin basis** in one line: "I'm about to [claim / give up / build on / offer options / send this] based on [memory / one attempt / an old conclusion / an unweighed pick / what I read and the reader didn't]."
2. **Do the cheap work** for each angle that fired. Angles stack.
3. **Come back with the receipt**: what you ran, read, or found.

Why: the user can't see what you didn't check. A claim built on memory reads exactly like one built on evidence, and they pay for it later.

**Skip** when the step is trivial and easy to undo, or the claim rests on output from this same turn. If you're arguing with yourself about whether it's trivial, it isn't.

**If the work flips an earlier answer, say so plainly.** Flipping after checking means this worked.

## Angles

| Angle | Before you… | The cheap work |
|---|---|---|
| check | claim done / fixed / found / pre-existing | verify it this session; reproduce "pre-existing" on a clean base |
| try | say can't / blocked / "say the word" | retry transients once, try the next tool, just do read-only things |
| rederive | build on a handoff or old conclusion | say where it came from and how old, re-check against current evidence |
| weigh | put options in front of the user | drop fake options, find prior art, tradeoffs with evidence, recommend |
| unpack | ask a question or offer options | define every ID and label for a reader who wasn't there |
| simplify | send a long reply | answer first, a few bullets, stop |

Full checklist per angle, the tool menu, the clean-room pass, and reply shapes: `references/angles.md`. For each angle you're running, read its checklist and any `<angle>:` section further down.

## Red flags: stop and run the core

- "I'm confident I already did this" / "the handoff says it's done"
- "that failure is probably pre-existing / flaky"
- "I can't from here" (after one try), or "say the word and I'll..."
- "we already decided this" (when?)
- "here are the options" (researched? readable cold?)
- a reply that needs a scroll before the answer

Excuses and counters: `references/rationalizations.md`. Worked examples: `references/examples.md`.
