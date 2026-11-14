# Woodpecker skill evals

Trigger sets for both woodpecker skills: `evals/eval_set.json` in each skill dir, 20 queries each, 10 should-trigger and 10 near-misses (GitHub Actions, Buildkite, Jenkins, Drone, CircleCI, local test failures, server admin, work on this plugin, and the sibling skill). Several positives name no Woodpecker tooling.

## Results (2026-10-17)

Description optimization loop, 5 iterations, 3 runs per query, `claude -p` single turn.

| Skill | Positives that triggered | False triggers | Best test score |
|---|---|---|---|
| investigating | 4-5 of 10 (8 of 10 on the last iteration at 1-in-3) | 0 of 10, every iteration | 5/8 (original: 4/8) |
| authoring | 1-3 of 10 | 0 of 10, every iteration | 4/8 (original: 4/8) |

Rewording the descriptions did not move recall, so the descriptions are unchanged. Same flat shape as `plugins/buildkite/skills/investigating-builds/evals/README.md`: treat it as a floor on false triggers, not a prediction of real recall.

## Baselines (no skill)

- 16 single-shot runs reading helper output (no pipeline, failed-but-ignored step, still running, empty `gh pr checks`): all correct. The state table adds nothing for those cases.
- 9 tool-using runs in a repo with `woodpecker-cli` off PATH: 0 of 6 investigation runs found the CLI (in that repo it was installed only via mise), none claimed a pass. 3 of 3 authoring runs linted through the `woodpeckerci/woodpecker-cli:v3` image and caught localhost vs service name.

## Re-running

The installed plugin answers instead of the harness's temp skill, so hide it:

1. Copy skill-creator's `scripts/` somewhere scratch.
2. Add `"--setting-sources", "project"` to the `claude -p` command in `run_eval.py`.
3. `python3 -m scripts.run_loop --eval-set <this file> --skill-path <skill dir> --model <model> --results-dir <dir>`, from a directory that has its own `.claude/`.

It needs the sandbox off (Python's process pool hits `sysconf`).
