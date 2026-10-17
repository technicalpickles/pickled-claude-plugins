---
name: come-on
description: Use when a reply will hand the user a result they'll act on or repeat to others. You MUST load this at the start of the turn, before other tools, when the user asks you to finish or fix something and confirm it works, report whether something is done, shipped, merged, fixed, or still broken, fetch or refresh data and report a value they need for other work, pick up work from a handoff, notes, or an earlier session, choose between approaches ("should we X or Y", "what would you do"), or summarize work for someone who wasn't there. Also load it whenever the user pushes back on something you said earlier in this conversation, like asking you to retry what you called failed or blocked, "is it really", "are you sure", "confirm first", asking whether you verified a claim, or asking what a term or label you used means. Load it even when you already plan to verify. Skip for a single command or edit the user fully specified where the reply is just its outcome, and for pure writing or explaining tasks.
argument-hint: "[check|try|rederive|weigh|unpack|simplify] [target]"
---

# come on

Don't stop short. Do the cheap work, then make it land.

## Mode

Arguments: "$ARGUMENTS"

- **Empty:** you're here on your own or the user said "come on". Pick the angles that fit the turn you're about to send (or the one the user is reacting to).
- **Starts with a mode** (`check`, `try`, `rederive`, `weigh`, `unpack`, `simplify`): run that angle on the last reply, plus any other that obviously applies. The rest of the arguments name the target: a claim, a reader (`unpack for my skip-level`), or a shape (`simplify for slack`).

## The core (every angle)

1. **List the loose claims.** Go through the reply you're about to send (or just sent) and pull out every statement the user will act on that you haven't verified this turn: a claim of done or fixed, a "can't", something inherited from a handoff or old conclusion, an option set you haven't weighed. Usually there are several. Each gets its own check.
2. **Do the cheap work for each one**, for each angle that fired. Independent checks run in parallel.
3. **Reply in this shape:**
   - The answer first, in plain words. If a check flipped something you said earlier, that comes first.
   - Then one line per claim: what you checked, what you found.
   - Then anything you couldn't check, and why.

Why: the user can't see what you didn't check. A claim built on memory reads exactly like one built on evidence, and they pay for it later.

**Skip** when the step is trivial and easy to undo, or the claim rests on output from this same turn. If you're arguing with yourself about whether it's trivial, it isn't.

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
