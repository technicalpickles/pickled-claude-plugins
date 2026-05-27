# github-actions

Plugin for investigating failing GitHub Actions runs. Mirrors the `buildkite` plugin's shape, scoped to investigation only (no workflow authoring, no fix loop).

## Skills

- **investigating-runs** — load when working with an existing GHA run (failed CI, red PR check, log dive).

## Helper

- **`gha-snapshot`** — Python script (stdlib-only) that wraps `gh run view` / `gh api` to produce a single readable failure summary. Invoked from the skill via `${CLAUDE_PLUGIN_ROOT}/scripts/gha-snapshot <ref>`.

## Requirements

- `gh` CLI installed and authenticated
- Python 3.9+

## Out of scope (v1)

- Authoring `.github/workflows/*.yml`
- Fix loops (verify → push → check → iterate)
- Monitoring/watching a running build
