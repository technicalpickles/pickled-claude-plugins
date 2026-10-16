# wait-for-it trigger evals

Measures whether the `wait-for-it` skill gets invoked: fires on "tell me when X
happens" / "monitor X" asks, stays quiet on everything else. Behavior evals
(does it arm the right watch?) don't exist yet.

## Cases

25 `claude plugin eval` cases, each
graded by a single `tool_used: Skill` grader matching `wait-for-it`, `min: 1`
(fire) or `max: 0` (quiet).

| Prefix | Count | What |
|---|---|---|
| `tune-*` | 14 (9 fire, 5 quiet) | Cold prompts. Iterate the description against these. |
| `holdout-*` | 6 (3 fire, 3 quiet) | Cold prompts. Check once per description revision; never quote them in the description. |
| `warm-*` | 5 (3 fire, 2 quiet) | Replays a synthetic 3-turn coding session (`history.jsonl`) before the prompt, to check late-session recall. |

The cold prompts are real phrasings from past sessions, de-identified. Most of
the real misses were compound asks where monitoring is the *second* half
("push. then monitor for PR reviews"): Claude does the first half, runs a
blocking `gh run watch`, and never loads the skill.

Every case allows only `Read`, `Glob`, `Grep`, and `Skill`, so they run on the
host without a VM.

## Running

Two harnesses, because they disagree in useful ways.

**`claude plugin eval` (isolated).** Only this plugin is installed, so the
skill has no competition. Optimistic.

```bash
cd plugins/wait-for-it
claude plugin eval . --tag tune --ablation none --runs 3 -j 4 \
  --trust-plugin --no-publish --max-cost-usd 6
```

Swap `--tag` for `holdout` or `warm`, or drop it for all cases.

**`trigger_eval.py` (full install).** Runs `claude -p` against your real
install, so the skill competes with every other skill and Bash is available.
Closer to how the real misses happened. Uses `trigger-evals.json` (the 20 cold
prompts; `note` holds the matching case name).

```bash
python3 plugins/second-brain/skills/capture/evals/trigger_eval.py \
  --eval-set plugins/wait-for-it/evals/trigger-evals.json \
  --plugin-src "$PWD/plugins/wait-for-it" \
  --skill wait-for-it --namespace wait-for-it \
  --cwd "$PWD" --label current --out <out>.json
```

Pass `--plugin-src` as an absolute path; `.` crashes it.

## Results

Recall = fire cases passing. Specificity = quiet cases passing. Each case runs 3 times.

| Run | Harness | Recall | Specificity | Cost |
|---|---|---|---|---|
| baseline, all 20 cold | trigger_eval.py | 6/12 | 8/8 | subscription |
| baseline, all 20 cold | plugin eval | 9/12 | 8/8 | $5.51 |
| v1, tune 14 | trigger_eval.py | 9/9 | 5/5 | subscription |
| v1, tune 14 | plugin eval | 9/9 | 5/5 | $4.33 |
| v2, all 20 cold | trigger_eval.py | 10/12 | 8/8 | subscription |
| v2, all 20 cold | plugin eval | 12/12 | 7/8 | $5.92 |

v2 is the shipped description. On holdout it scores 5/6 in each harness, failing
on different cases:

- **trigger_eval.py** misses `holdout-fire-02` ("push. then monitor for PR
  reviews"), 0/3. The compound-ask shape again.
- **plugin eval** false-fires on `holdout-quiet-01` ("fix CI on this branch and
  keep pushing until it's green"), 3/3. Under full install it's 0/3, likely
  because `ci-cd-tools:fixing-ci` is there to claim it.

Warm cases haven't been run yet.

Raw output is in `results/`: `*-cold.json` from plugin eval,
`*-cold-trigger_eval.json` from trigger_eval.py.

## Caveats

These are cold, single-prompt evals, so treat them as a floor on real-world
behavior, not a prediction. The real check is querying past sessions for
monitoring asks that didn't load the skill, after the plugin has been installed
for a while. If recall plateaus across description revisions, see "Description
Tuning Has a Structural Ceiling" in the repo `CLAUDE.md`.
