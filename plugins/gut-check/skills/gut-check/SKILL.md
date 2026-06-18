---
name: gut-check
description: Use when about to lock in a non-trivial or hard-to-reverse decision, fire AskUserQuestion to offload a call, proceed on your own preferred option, or assert something is done / found / tested / fixed / "that's how it works" — especially when the basis is memory, the handoff, the first framing, or an unchecked assumption rather than something verified this session. Also invoked as /gut-check. Use even when you feel confident; confidence is the symptom, not the all-clear.
---

# Gut Check

## The spine

Don't lock in a decision or assert a fact from a thin basis: memory, the handoff,
the first framing, an unexamined pick. Ground it first, then proceed.

**Violating the letter of this is violating the spirit of it.** "I'm confident, so
I can skip the check" is the exact failure this skill exists to catch.

## When this fires

You are about to do one of these AND the basis is thin (not verified this session):

- Lock in a non-trivial or hard-to-reverse decision
- Fire AskUserQuestion to offload a decision you could ground yourself
- Proceed on your own preferred option without weighing alternatives
- Assert something is done / found / tested / fixed / "that's how X works"

Skip it for trivial, reversible steps, and for claims already backed by output you
produced **this turn**. When unsure whether it's trivial, it isn't, engage.

## Shared opening (both modes)

Name the thin basis in one line: "I'm about to [decide X / claim Y] based on
[memory / the handoff / first framing / my own pick]." Naming it is what flips you
from asserting to grounding.

Then pick the mode: grounding a **decision** → DECIDE. Grounding a **fact** → VERIFY.

## DECIDE mode

1. **Validity gate.** For each option, is it even real/valid? Drop the bogus ones.
2. **Consult existing context.** Read the relevant ADRs, docs, code, prior
   decisions. The answer is often already settled there, don't reason in a vacuum.
3. **Per-option tradeoffs.** One by one: pros/cons, plus effort (easier/harder)
   and durability (long-run). Not a blurry summary.
4. **Ranked recommendation.** State a lean and why, give something to react to.
5. **Hand the call back.** Surface the recommendation; let the user decide. Do the
   thinking; don't offload the thinking, and don't seize the deciding.

## VERIFY mode

1. **State the claim precisely.** "I'm claiming X is done/found/true."
2. **Check it this session.** Read the file, run the command, grep the evidence.
   Memory and the handoff do not count.
3. **Report grounded.** "Confirmed, here's the evidence" / "No, not actually done"
   / "Partial: X yes, Y no." Show the receipt.

**Hard rule, the pre-existing dismissal:** never call a failure *pre-existing,
unrelated, or flaky* without reproducing it on a clean base **this session** (run on
`main`, `git stash` + test, or `git blame` the lines). This is the highest-value
case: such dismissals close off investigation and almost always go unchecked. "It's
probably pre-existing" is a trigger thought, not a conclusion.

## Honesty rule (both modes)

If grounding flips your answer, say so plainly. Reversing your own earlier pick
after checking is the skill working, not a failure.

## Red flags, STOP and engage

If you catch yourself thinking any of these, you're rationalizing:

- "I'm confident I already did this"
- "I remember the handoff said..."
- "it's basically done"
- "the obvious choice is..."
- "that failure is probably pre-existing / unrelated / flaky"
- "the user's in a hurry, I'll skip the check"

All of these mean: ground first. For the full set of excuses and their counters,
read `references/rationalizations.md`. For worked DECIDE/VERIFY examples, read
`references/examples.md`.
