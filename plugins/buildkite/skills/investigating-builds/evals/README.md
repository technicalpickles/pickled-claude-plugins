# investigating-builds eval artifacts

These files support tuning the skill description. The description is what determines whether Claude invokes the skill for a given user query, so keeping it well-tuned matters.

## Files

- `eval_set.json` — 20 queries with `should_trigger` labels. Positives cover real Buildkite investigation intents (`bk` CLI, `bktide`, buildkite.com URLs, "why did this build fail", flaky-spec analysis, reproducing CI jobs locally). Negatives cover three near-miss categories:
  - **YAML authoring** (should route to `buildkite:developing-pipelines`)
  - **Meta-work on the plugin itself** (editing SKILL.md, pickled-claude-plugins PRs)
  - **Adjacent-but-unrelated** (GitHub Actions, PR review, app code, `~/.bk/config.yml` setup)

## Why the description matters

Session transcript analysis on the original description showed many sessions with real Buildkite activity (`bk` CLI, `bktide`, buildkite.com URLs) where the skill never fired. The old text used generic CI language ("working with Buildkite CI", "investigating failures") without the concrete trigger vocabulary users actually reach for. A formal eval confirmed 0% recall on positives: precision was 100%, but the skill triggered on none of the 10 should-trigger queries across 3 runs each.

The replacement description adds concrete trigger vocabulary (named tools, URL patterns, natural intent phrasings like "why did this build fail") and explicit negatives for the two near-miss categories that share "buildkite" as a keyword.

## Re-running the eval

From the skill-creator plugin:

```bash
cd ~/.claude/plugins/cache/claude-plugins-official/skill-creator/*/skills/skill-creator

uv run --with anthropic --with 'httpx[socks]' -- python3 -m scripts.run_loop \
  --eval-set path/to/eval_set.json \
  --skill-path path/to/plugins/buildkite/skills/investigating-builds \
  --model claude-opus-4-7 \
  --max-iterations 5 \
  --verbose
```

Requires `ANTHROPIC_API_KEY` for the description-improvement step, or patch `improve_description.py` to use `claude -p` via subprocess.

## Caveat on the formal eval

In the initial tuning run, all 5 iterations scored identically on train (6/12) and test (4/8). This flatness suggests the isolated single-turn `claude -p` harness may not distinguish descriptions well for substantive multi-step queries, since Claude needs the real agentic context to decide on skill invocation. Treat the eval as a floor (catches obvious false triggers) rather than a ceiling (reliable recall prediction). Real validation is using the skill in a normal session.
