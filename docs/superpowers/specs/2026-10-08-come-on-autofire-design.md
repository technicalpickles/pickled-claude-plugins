# come-on: consolidate to one skill and fix auto-firing

**Date:** 2026-10-08
**Branch:** `come-on-plugin` in pickled-claude-plugins (draft PR https://github.com/technicalpickles/pickled-claude-plugins/pull/146)
**Method:** superpowers:writing-skills (RED/GREEN/REFACTOR) + skill-creator (realistic near-miss queries, old-skill baseline, human review of outputs)

## Problem

In the 2026-10-08 scenario sweep the `come-on` skill fired in 4 of 10 behavior scenarios, mostly when the prompt itself asked for the angle. The trigger evals (18/18) overstate it because the description was tuned against those exact prompts, which quote user pushback. Real agent turns carry no such cue.

There's a second, larger risk that the evals can't show. Claude Code's skill listing has a budget (1% of the context window). When it overflows, descriptions are dropped starting with the **least-invoked** skills, and the skill stays listed by name only. A brand-new auto-fire skill sits at the bottom of that ranking. In Josh's normal setup most skills already list name-only. Plugin skills can't be pinned with `skillOverrides`.

## Decisions

### 1. One skill with modes

- Merge the six `come-on-*` entry-point skills into `come-on` and delete their dirs. Add `argument-hint: [check|try|rederive|weigh|unpack|simplify]`.
- **Routing goes first in the body.** `$ARGUMENTS` empty: pick the angles that apply (the auto-fire path). First word is a mode: run that angle on the last reply (plus any other that obviously applies), and the remaining words name the target.
- Why: manual `/come-on <mode>` uses accrue to the one skill, which should keep its description in the listing. It also removes the second Skill hop, since today each entry point tells Claude to load `come-on`. And the listing goes from seven names to one. Unverified: that user-typed invocations count toward the listing's usage ranking the same way model-initiated ones do. The docs say "the skills you invoke least".
- Cost: no per-mode `/come-on-check` tab-completion.

### 2. SKILL.md under 500 words

- SKILL.md keeps the routing, the core loop (name the thin basis, do the cheap work, show the receipt), the skip rule, the honesty rule, and one line per angle.
- Per-angle detail moves to `references/angles.md` (already exists), with a pointer telling the agent when to read it.
- Tone: explain the why instead of all-caps MUSTs (skill-creator). Keep the rationalization counters in `references/rationalizations.md` (writing-skills).

### 3. Description rewrite

- Starts "Use when…", third person, under 1024 characters (currently 1189).
- Triggers are written from the agent's own position: about to claim done, fixed, found, or pre-existing without checking this session; about to say can't or blocked after one attempt; about to build on a handoff, old design, or earlier conclusion; about to put a choice in front of the user, or one full of labels they never saw; about to send something long without the answer up top.
- A short tail of user phrasings stays ("come on", "did you check", "try again", "tl;dr").
- Pushy (skill-creator), with at most one clause on what the skill does and no process steps (writing-skills).

### 4. Evals

All evals stay on `claude plugin eval`. skill-creator's `run_eval.py`/`run_loop.py` aren't used: their synthesized slash command isn't model-visible, so every query scores near zero regardless of the description, and `run_loop.py` needs an API key.

- **Trigger set (new, replaces `trigger-*`/`no-trigger-*`):** 20 realistic queries in skill-creator style, with detail, backstory, and casual phrasing. About 10 should-trigger, most with no pushback words, where the natural move is to stop short. About 10 near-miss should-not-trigger cases that share come-on's vocabulary but don't need it (a "try again" on an idempotent rerun the user asked for, a "tl;dr" of a doc the user wrote, a "did you check" answered by output already in this turn). Josh reviews the set in skill-creator's `assets/eval_review.html` before any runs.
- **Split:** fixed 60/40, prefixed `tune-` (12) and `holdout-` (8). I don't read holdout prompts or graders while iterating on the description. The old trigger dirs are deleted; git has them.
- **Scenarios:** the 10 `scn-*` cases are also holdout. The `skill-fired` indicator is the primary metric, and grader scores are secondary.
- **Mode routing:** 3 cases (`/come-on weigh …`, `/come-on check …`, `/come-on unpack …`) checking that the right angle runs.

### 5. Loop

1. **Snapshot:** copy the current `skills/come-on/` to the eval workspace as `old-skill` (the skill-creator baseline for improving an existing skill).
2. **RED:** run the holdout triggers + `scn-*` against the old skill in the colima `plugin-eval` VM (Bash-granting runs must run there because the host ~/.ssh layout trips the eval harness). Record firing per case. Bump to 5 runs on the cases that swung between earlier sweeps.
3. **GREEN:** consolidate, trim, and rewrite. Iterate on the tune set only. Then run the holdout + scenarios once against the new skill.
4. **Human pass:** build the skill-creator viewer (`eval-viewer/generate_review.py --static`) over old vs new scenario outputs. Josh reads the outputs and leaves feedback.
5. **REFACTOR:** if holdout firing is still weak, pull the rationalizations from the traces, make one more description pass, re-run the holdout, and stop.
6. Update the README (modes table, Testing status with the new numbers), then commit to `come-on-plugin` with no internal tracker IDs (public repo).

**Success:** holdout firing is clearly above the old skill's (the RED number, same cases, same run count), near-miss false-fires stay at or below the old rate, and mode-routing cases pass.

## Out of scope

- **Hook nudge** (`Stop` / `UserPromptSubmit`): this becomes a follow-up if holdout firing stays weak after REFACTOR. Skill-scoped `hooks` frontmatter doesn't help because it only activates after the skill is invoked.
- **Listing-budget simulation** (a VM run with about 200 filler skills): a separate follow-up.
- Task 11 (install, dotfiles `dev` profile, measurement) still waits on the merge.

## Open questions

- Do user-typed `/skill` invocations count toward the listing's usage ranking? This is the main argument for consolidating. It can be probed later via `pickletown:claude-binary-spelunking`.
- Can `claude plugin eval` filter cases by name or tag, or does the prefix convention have to drive this with separate runs? Check `claude plugin eval --help` during planning.
