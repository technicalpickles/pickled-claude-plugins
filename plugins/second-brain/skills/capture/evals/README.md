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
