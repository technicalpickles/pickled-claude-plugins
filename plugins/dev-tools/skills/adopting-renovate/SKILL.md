---
name: adopting-renovate
description: Use when adding Renovate to a repo, moving a repo's renovate.json onto the shared technicalpickles/renovate-config presets, or previewing what Renovate would open before a config merges. Detects ecosystems and CI, writes the one-line config, dry-runs it, and opens the PR.
---

# Adopting Renovate

Policy lives in the shared presets at [technicalpickles/renovate-config](https://github.com/technicalpickles/renovate-config). This skill is the procedure for applying them to one repo. When a lesson changes policy, fix the preset, not the repo.

## Prerequisites

- Renovate CLI: `npm:renovate` in the global mise tools (`mise exec npm:renovate -- renovate --version`). `mise install npm:renovate` on the command line resolves `latest` and ignores config options, so use plain `mise install`.
- `gh` authenticated with read access to the repo.
- The Renovate GitHub app has access to the repo. A config does nothing without it; see Gotchas.

## Procedure

### 1. Detect ecosystems

```sh
gh api repos/<owner>/<repo>/contents -q '[.[].name]|join(" ")'
```

| Files | Manager |
|---|---|
| `package.json`, `package-lock.json` | npm |
| `Cargo.toml`, `Cargo.lock` | cargo |
| `go.mod` | gomod |
| `pyproject.toml`, `uv.lock` | pep621 / uv |
| `Gemfile`, `*.gemspec` | bundler |
| `mise.toml`, `.mise.toml` | mise |
| `Dockerfile`, `.devcontainer/` | dockerfile |
| `.github/workflows/*.y*ml` | github-actions |

Flag any mise tool pinned to `"latest"`: Renovate cannot bump it. Pin it in the same PR.

### 2. Decide on automerge

Automerge only when `main` has required status checks.

```sh
gh api repos/<owner>/<repo>/branches/main/protection -q '.required_status_checks.contexts|join(",")'
```

Empty or a 404 means PRs only. No `pull_request` workflows at all means PRs only and say so in the PR body.

### 3. Write `renovate.json`

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "github>technicalpickles/renovate-config",
    "github>technicalpickles/renovate-config:mise",
    "github>technicalpickles/renovate-config:automerge"
  ]
}
```

Include only the presets that apply: `:mise` when there is a mise config, `:automerge` per step 2, `:lockfile` only if asked. Put local overrides below `extends`. A mise config outside the repo root needs `"mise": {"managerFilePatterns": ["/^config/mise/.+\\.toml$/"]}`.

Validate it:

```sh
mise exec npm:renovate -- renovate-config-validator renovate.json
```

### 4. Dry-run before merging

This lists the branches Renovate would open and changes nothing. The git clone fails inside the Claude Code sandbox (proxy aborts HTTPS), so this one command needs the sandbox off. It only reads the repo.

```sh
cat > "$SCRATCH/config.js" <<'EOF'
module.exports = { extends: ["github>technicalpickles/renovate-config", "github>technicalpickles/renovate-config:mise"] };
EOF
RENOVATE_CONFIG_FILE="$SCRATCH/config.js" RENOVATE_TOKEN="$(gh auth token)" \
  LOG_LEVEL=debug LOG_FORMAT=json RENOVATE_PLATFORM=github RENOVATE_DRY_RUN=full \
  RENOVATE_REPOSITORIES=<owner>/<repo> RENOVATE_ONBOARDING=false RENOVATE_REQUIRE_CONFIG=optional \
  mise exec npm:renovate -- renovate > "$SCRATCH/run.log" 2>&1

jq -r 'select(.msg=="branches info extended")|.branchesInformation[]|"\(.branchName) | \(.prTitle // "")"' "$SCRATCH/run.log"
jq -r 'select(.msg|test("creation is disabled because dependencyDashboardApproval"))|.msg' "$SCRATCH/run.log"
```

Read the output:

- Majors show in the branch list but are held: "creation is disabled because dependencyDashboardApproval=true". They only become PRs when someone ticks them on the Dependency Dashboard.
- The PRs that will actually open are the grouped ones plus a single "pin dependencies" PR. More than a handful means a grouping rule is missing from the preset.
- Check that every ecosystem from step 1 appears. A manager that detected files but planned nothing deserves a look (see the `go` gotcha).

### 5. Open the PR

Use the `git:pull-request` skill. If Renovate already opened its own "Configure Renovate" onboarding PR, ours replaces it: merge ours and the onboarding PR autocloses. Mention the preset repo in the body, and the dry-run branch count.

### 6. After it merges

Enable dependency alerts so security fixes can be found (they skip the cooldown and the schedule):

```sh
gh api -X PUT repos/<owner>/<repo>/vulnerability-alerts
```

Look for the Dependency Dashboard issue and the first grouped PRs after the next scheduled run (Monday before 5am UTC). If nothing appears, the app is probably not installed on the repo.

## Gotchas

- **The app must be installed per repo.** No Renovate PRs, branches or Dependency Dashboard issue after a scheduled run means the app has no access. `gh` cannot list installations (needs a GitHub App token); check the repo's access list in GitHub settings or the Mend portal.
- **`extractVersion` on every mise tool drops updates.** A rule that strips the `v` prefix must be scoped with `matchDepNames: ["github:**"]`. Unscoped, it silently removed `go` updates. The `:mise` preset already scopes it; a hand-rolled rule may not.
- **Cooldown vs provenance.** `minimumReleaseAge` (7 days in the base preset) holds every package, including your own tools unless the preset exempts them. Renovate reads npm provenance only to add a caution note to a PR body when a new version loses an attestation, and never blocks on it.
- **mise has its own trust check.** mise's aube installer can reject a transitive npm dependency that lost provenance (`trustPolicy=no-downgrade`). Vet the release, then exclude the exact `package@version` via `trust_policy_excludes` on that tool, with the reasoning in a comment.
- **Public presets only.** `github>` presets are fetched from GitHub; keep the preset repo public.
- **Dry-run caveat.** The dry-run does not prove automerge fires or that a lockfile like `go.sum` comes out right. Watch the first real PR.
