# Worked examples

Real before/after from session history (the patterns this skill generalizes).

## VERIFY, pre-existing dismissal (the marquee case)

**Thin basis:** "three specs fail, probably pre-existing."
**Grounded:** ran the specs on `main` locally with none of the change applied →
"Definitive proof. On the main branch locally, fails with the identical error."
The claim turned out true, but only the check made it trustworthy. Without the
check it's a guess that happens to close off investigation.

## VERIFY, done from memory

**Thin basis:** "yes, that's already captured."
**Grounded:** "rather than trust my memory, let me actually look" → read the file →
"No, we never captured the investigation outside this chat." The check flipped the
answer.

## DECIDE, re-deliberate off your own favorite

**Thin basis:** wrote the design around a preferred option (B) and called it
recommended.
**Grounded:** validity gate + tradeoffs (pros/cons + effort + durability) against
the project's own axioms → the analysis reversed the pick: "on your own axioms, A is
the cleanest." User chose A. Re-grounding flipped the model's own recommendation.

## DECIDE, don't punt, ground then hand back

**Thin basis:** about to fire AskUserQuestion to offload a "product fork."
**Grounded:** "let me actually dig into the project's own decisions rather than punt
it to you" → read the relevant ADR → the architecture's invariant made one option
the only consistent choice. Decision derived, not offloaded.
