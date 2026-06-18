# gut-check

A discipline skill: **ground before you act.** It fires when you're about to lock in
a non-trivial decision or assert a fact (done / found / tested / pre-existing) from a
thin basis, memory, the handoff, the first framing, an unexamined pick, and makes you
ground it first.

Two modes:

- **DECIDE** — weigh the real options with tradeoffs, recommend, and hand the call
  back (don't punt via AskUserQuestion, don't silently implement your favorite).
- **VERIFY** — check the claim this session and show the receipt. Hard rule: never
  call a failure pre-existing/unrelated/flaky without reproducing it on a clean base.

Also invocable as `/gut-check`.

## Provenance

Built from transcript-mining of real sessions where the user repeatedly pushed back
on the model acting from a thin basis (deliberate-before-deciding, verify-before-
believing). The pre-existing-failure dismissal is the highest-value case it guards:
in the corpus the model made hundreds of such claims and they almost always went
unchallenged.

## Testing status

`test/` and `skills/gut-check/evals/` hold pressure scenarios, a fixture, and a
skill-evals config. They are scaffolding. A clean synthetic baseline proved hard to
reproduce (current models self-ground when a check is cheap; the real failure mode
lives in expensive-check / sunk-cost / long-context conditions). Validation is
therefore by **dogfooding** in real sessions rather than a synthetic eval gate. The
scaffolding is kept for future refinement.
