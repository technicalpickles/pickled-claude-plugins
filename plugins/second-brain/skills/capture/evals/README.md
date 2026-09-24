# Evals for `capture`

## Behavior eval: `no-route-offer`

Permanent regression fixture for Step 4 ("leave it in the inbox for
`process-inbox` to route" - capture must never ask about routing per note).
Lives at `scenarios/no-route-offer/scenario.yaml`, run via the `skill-evals`
harness (a separate tool, not `trigger_eval.py`):

```bash
cd /path/to/skill-evals
uv run skill-evals \
  --plugin-dir /path/to/pickled-claude-plugins/plugins/second-brain \
  --config /path/to/pickled-claude-plugins/plugins/second-brain/skills/capture/evals/eval_config.yaml \
  --scenarios-dir /path/to/pickled-claude-plugins/plugins/second-brain/skills/capture/evals/scenarios \
  --project-root /path/to/pickled-claude-plugins/plugins/second-brain \
  --scenario no-route-offer --trials 1
```

Confirmed 2026-08-28: passes 100% (behavior + tool_calls checks) against the
current (fixed) `capture/SKILL.md` across 3 real runs. Read the "known quirk"
comment at the top of `scenario.yaml` before trusting the transcript's own
narrative of success/failure - the model sometimes reports Write/Edit as
"denied" even when the harness's own results JSON shows the mock matched and
returned success. That's a separate, filed `skill-evals` harness issue, not a
`capture` bug, and doesn't affect this scenario's actual pass/fail (the checks
are scoped to routing language and the absence of a `sb note move` call,
neither of which the denial narrative touches either way).

# Trigger evals for `capture`

Measures whether the skill actually fires on real user phrasings. Queries in
`trigger-evals.json` are verbatim prompts from 50 real vault sessions (2026-07-27 → 08-14), mined
with `cq`, including the recurring `ntoe` typo. 10 should-trigger, 10 near-miss should-not-trigger.

## The headline result

| Condition | Recall (10 positives) | Specificity (10 negatives) |
|---|---|---|
| Vault CLAUDE.md pointer, scoped to "create a note" | 70% | 100% |
| **No pointer in vault CLAUDE.md** | **0%** | n/a |
| Pointer widened to "create **or find** a note" | **100%** | 100% |

Raw runs in `results/`. 3 runs per query, trigger threshold 0.5.

Two things follow, and they matter more than the skill's own wording:

1. **The SKILL.md description has no independent pull.** Thirty runs, zero triggers, on phrasings
   as on-the-nose as "read \<url\> and make a note for it". Time spent tuning description prose is
   wasted; the vault CLAUDE.md pointer is the mechanism. That's why the pointer ships in
   `templates/vault-claude-md.md` with a "keep this section" warning.
2. **Scope the pointer to every intent you want caught.** With the pointer scoped to *create*,
   all three pure-lookup queries failed 0/3. Widening the heading and adding a lookup bullet took
   them to 2/3, 3/3, 3/3 with no loss of specificity. The pointer's wording is doing the routing,
   so an intent it doesn't name is an intent that won't fire.

This likely generalizes to the plugin's other skills (`route`, `enrich`, `connect`, `ingest`),
which were invoked once total across those same 50 sessions while ~150 notes were written by hand.
Worth measuring before assuming those skills are unwanted rather than unreachable.

## Running them

```bash
./trigger_eval.py \
  --eval-set trigger-evals.json \
  --plugin-src ../../.. \
  --skill capture --namespace second-brain \
  --cwd /path/to/a/vault \
  --runs 3 --workers 6 --turns 2 \
  --out results/$(date +%F)-my-change.json
```

Notes on getting trustworthy numbers:

- **Don't run against your real vault.** At `--turns 3` the runs will happily create notes in your
  inbox. Use a throwaway vault-shaped directory: `.obsidian/`, a CLAUDE.md, a couple of real-ish
  notes. `--turns 2` is enough to observe triggering.
- **Isolate the variable you care about.** Triggering is dominated by the cwd's CLAUDE.md, so
  compare arms that differ in exactly one thing. The 0%-recall arm above is just the widened arm
  with the pointer section deleted.
- `--description` patches the description in a temp copy, for A/B without touching SKILL.md.

## Site-specific links (2026-09-19)

Added 4 queries for the site-playbook work: bare YouTube link + "make a note", Reddit permalink +
"atomic note", bare tweet link + "capture this" (3 positives), and a YouTube link asked as a question
with "dont save anything" (1 near-miss). **These are synthetic**, not mined from real sessions (their
`note` fields say so); replace them with verbatim prompts as real ones accumulate. The set is now 24
queries (13 positives, 11 negatives).

| Query | Baseline (pointer before) | Widened pointer |
|---|---|---|
| YouTube link, make a note | 3/3 | 3/3 |
| Reddit permalink, atomic note | 3/3 | 3/3 |
| Bare tweet link, capture this | 3/3 | 3/3 |
| YouTube link, question only (negative) | 0/3 | 0/3 |

- The **baseline arm ran only the 4 new queries** against the old pointer
  (`results/2026-09-19-site-baseline.json`). The widened arm ran the full 24
  (`results/2026-09-19-site-pointer.json`); the existing 20 are compared to
  `results/2026-08-14-pointer-widened.json`.
- Existing 10 positives: all 3/3 (two that were 2/3 on 2026-08-14 went to 3/3, noise). Existing negatives
  (10) and the new one: all 0/3, specificity 100%. No regressions.
- Caveat: the new positives already fired 3/3 before the pointer change (the pointer's "read
  \<url\> and make a note" and "capture" wording plus explicit note intent was enough), so this set
  can't show lift from the widening. It guards against regression and covers the bare-link phrasing;
  a link with no verb at all is not measured here.
- Harness note: `--plugin-src ../../..` crashes (`Path("../../..").name` is `..`); pass the resolved
  absolute path to `plugins/second-brain` instead.

## Why not skill-creator's `run_eval.py`

`skill-creator` ships `scripts/run_eval.py` for exactly this job. It does not work for plugin
skills, and it fails *silently* — it reports zeros, which reads as "bad description" rather than
"broken harness."

It injects the skill under test by writing a stub to `<project_root>/.claude/commands/<name>.md`,
on the premise (in its own docstring) that this makes it "appear in Claude's available_skills
list." That premise is false on current Claude Code: project `commands/` entries are *user*-invocable
slash commands, not model-invocable skills. Verified 2026-08-14 by planting a `zzzprobe` command and
asking the model whether it could see it — it answered NO and reached for a real installed skill
instead. So no query can ever trigger, regardless of description quality.

Its companion `scripts/run_loop.py` (automated description improvement) additionally requires
`ANTHROPIC_API_KEY`, since it calls `anthropic.Anthropic()` directly rather than going through
`claude -p`.

`trigger_eval.py` keeps skill-creator's method — realistic verbatim queries, near-miss negatives,
N runs per query, threshold on trigger rate — and swaps the injection for `claude --plugin-dir`
against a temp copy of the plugin, so what gets measured is the artifact that ships.

One `--plugin-dir` gotcha it works around: **an installed plugin of the same name wins.** Pointing
`--plugin-dir` at a tree containing `second-brain` while `second-brain` is installed silently loads
the *installed* copy, so local edits appear to do nothing. The harness copies the plugin to a temp
dir to dodge this.
