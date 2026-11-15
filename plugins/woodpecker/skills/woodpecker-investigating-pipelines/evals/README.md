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

## Results (2026-11-14): hooks and description changes

Claude Code 2.1.322, Sonnet, `claude -p --plugin-dir <plugin> --setting-sources project`, counting a `Skill` call to a woodpecker skill.

**Single-turn trigger sets**, run from a repo with a `.woodpecker.yml`: 10 of 10 positives for both skills with and without the hooks, so this harness no longer separates them (the October numbers above came from skill-creator's harness on an older Claude Code). False triggers: 1 of 10 for investigating with the hooks (a Drone question), 0 without; 0 of 10 for authoring either way. The other negatives that loaded a woodpecker skill loaded the sibling one, correctly.

**Multi-turn scenarios** modeled on a real session where neither skill loaded: cwd with no Woodpecker config, the Woodpecker repo in a sibling directory, a stub `gh` whose `pr checks` shows only `ci/woodpecker/push/woodpecker`, and prompts that never say "Woodpecker". 5 runs per cell.

| Prompt | origin/main | new descriptions, no hooks | new descriptions + hooks |
|---|---|---|---|
| "I've added the automerge token secret for PR 68. See if we can test that the step works now." | 0/5 | 5/5 | 5/5 |
| Held out: "I only see one CI check on PR 68. Did the PR run actually happen?" | 5/5 | 5/5 | 5/5 |
| "Add a dependabot auto-merge step to the CI config in ../app ... what should I set on the secret?" | 5/5 | 5/5 | 5/5 |
| Held out: "What do I configure, in the repo's CI file and on the CI server, to get the step a token?" | 5/5 | 5/5 | 5/5 |

With the October descriptions and the hooks, the first prompt loaded a woodpecker skill 5 of 5 times against 1 of 5 without the hooks, but the PostToolUse pointer sent it to the authoring skill every time, because the task mentioned a secret. Rewording the pointer and the descriptions fixed the routing. In these scenarios the descriptions now carry the fix and the hooks add nothing measurable; the hooks stay as a backstop for sessions where descriptions miss, as the October trigger sets did.

## Re-running

The installed plugin answers instead of the harness's temp skill, so hide it:

1. Copy skill-creator's `scripts/` somewhere scratch.
2. Add `"--setting-sources", "project"` to the `claude -p` command in `run_eval.py`.
3. `python3 -m scripts.run_loop --eval-set <this file> --skill-path <skill dir> --model <model> --results-dir <dir>`, from a directory that has its own `.claude/`.

It needs the sandbox off (Python's process pool hits `sysconf`).
