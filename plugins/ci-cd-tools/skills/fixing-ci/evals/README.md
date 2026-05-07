# fixing-ci eval artifacts

These files support tuning the skill description. The description determines whether Claude invokes the skill for a given user query.

## Files

- `eval_set.json` — 16 queries with `should_trigger` labels.
  - **Positives** (10): real fix-loop intents (fix CI, make green, iterate on a build, "still red after my push", lockfile/lint/type fixes paired with push intent).
  - **Negatives** (6) cover near-miss categories:
    - **First-time investigation without fix intent** ("why did this fail") — should route to `buildkite:investigating-builds`
    - **Cross-build analytics** (pass/fail summaries) — should route to `buildkite:investigating-builds`
    - **Pipeline YAML authoring** — should route to `buildkite:developing-pipelines`
    - **Non-Buildkite CI** (GitHub Actions)
    - **PR review** — different domain
    - **Meta-work on the skill itself**

## Why the description matters

The trigger description distinguishes "I want to fix CI" from "I want to understand CI." Both involve build URLs and failure analysis, but the fix-loop adds verify-locally and iterate-and-push behaviors. The description leads with concrete trigger phrases ("fix CI", "make CI green", "iterate") and explicitly carves out the investigation-only case as a should-NOT.

## Re-running the eval

From the skill-creator plugin (requires `ANTHROPIC_API_KEY` or a `claude -p` patch — see the buildkite/investigating-builds eval README):

```bash
cd ~/.claude/plugins/cache/claude-plugins-official/skill-creator/*/skills/skill-creator

uv run --with anthropic --with 'httpx[socks]' -- python3 -m scripts.run_loop \
  --eval-set <repo>/plugins/ci-cd-tools/skills/fixing-ci/evals/eval_set.json \
  --skill-path <repo>/plugins/ci-cd-tools/skills/fixing-ci \
  --model claude-opus-4-7 \
  --max-iterations 5 \
  --verbose
```

## Caveat

As noted in the buildkite/investigating-builds eval README, the formal eval is a floor (catches obvious false triggers), not a ceiling. Real validation is using the skill in a normal session.
