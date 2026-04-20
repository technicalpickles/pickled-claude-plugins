# Iteration 1 — with-skill results

## Run cost

| Eval | Baseline tool calls | With-skill tool calls |
|------|---------------------|------------------------|
| explicit-pr-ref | 9 | 20 |
| ambient-pr-context | 8 | 11 |
| cold-reorient | 21 | 16 |

With-skill runs trade more tool calls against the pure-fetch baselines because they now produce the structured artifact (multiple Edit calls to fill verdict/reasoning/plan slots). Cold-reorient is the interesting one: it used *fewer* calls than the baseline because it stopped drifting into CI/merge-state exploration.

## What the skill delivered

All three with-skill runs:

- Wrote to the standard `.scratch/pr-reviews/603/threads.md` path (baselines each invented their own filename).
- Applied the verdict rubric (✅/❌/💡/❓) per thread — the core gap the skill was designed to close.
- Attached reasoning and plan per thread.
- Kept the `(tentative)` label on verdicts (shallow pass, as directed).
- Stayed in scope — no drift into merge conflict, CI, or approval state even in the cold-reorient case.
- cold-reorient wrote a proper `## Summary` section since the context was cold (1 paragraph, tight).
- ambient-pr-context respected reviewer scoping — only triaged rubberduck203's threads.

## Bugs found by the eval loop

**1. `fetch.sh` trap unbound variable on exit** — all three runs reported it. The `trap 'rm -f "$graphql_file" "$comments_file"' EXIT` referenced locals that were out of scope when the trap fired, so under `set -u` the script exited 1 even though the doc was written successfully. Fixed by expanding paths into the trap string eagerly (commit `058841f`).

## Residual observations (not blocking)

**1. ambient-pr-context left an out-of-scope thread half-filled.** The user asked about rubberduck203 only, and the subagent correctly triaged rubberduck203's two threads — but left the bot's third thread with `_pending triage_` placeholders rather than omitting it or marking it as out-of-scope. The skill's reviewer-scoping guidance could be more explicit about what to do with other-reviewer threads: drop them entirely from the doc, or annotate "(not addressed this pass — @user asked about rubberduck203)".

   **Decision:** leave for now. This is a subtle nudge, and heavy-handed directions here could backfire ("the skill tells me to suppress information"). Revisit if it recurs.

**2. "General comments" rendering keeps raw HTML comments and Buildkite URLs.** The Fresh Eyes bot's issue comment contains `<!-- fresh-eyes-review -->`, markdown images, links to build artifacts, etc. — all preserved verbatim. It's noisy but not wrong; the user can still read through it. Trimming or summarizing it is out of scope for a render script that shouldn't opinionate about content.

**3. Thread count discrepancy across runs.** All three with-skill runs saw 3 unresolved threads; a later smoke test after the trap fix saw 4. The PR's thread state is changing over time (comments being resolved, new ones added). Not a skill issue — just live data.

## Verdict

Ship iteration 1. The structural gaps (verdict rubric, plan, tentative marker, output location, scope discipline) are all closed. Residual observations are minor and speculative.
