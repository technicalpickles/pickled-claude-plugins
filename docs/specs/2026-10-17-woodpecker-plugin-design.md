# Woodpecker plugin: design

Status: draft. The CLI approach below was spiked against a live server on 2026-10-17. Sections say which claims were observed and which are still open.

[Woodpecker](https://woodpecker-ci.org) is a self-hosted CI server. It watches a git forge (GitHub, Gitea, Forgejo and others), runs pipelines defined in `.woodpecker.yml`, and reports results back as commit statuses. This repo has plugins for Buildkite and GitHub Actions but nothing for Woodpecker, even though the author runs it for several private projects.

This doc says what a `woodpecker` plugin should do, how it gets its data, and where the hard cases are.

## The problem

Claude can see that a Woodpecker pipeline failed. It can't see why.

- **Status is easy.** On GitHub, `gh pr checks` reports "Pipeline failed".
- **Logs were blocked.** The server's REST API answers 401 without a token, and the browser isn't signed in. Before the CLI was set up, the human pasted failing logs by hand.

Tracked in taskwarrior as `7acce601-5ea8-4105-8dfc-9cb650a6ef58` (CLI and skill) and `a6e43c56-b920-4ddf-902a-69299648cdf3` (the plugin).

## Decision: wrap `woodpecker-cli`

The plugin drives the official CLI and skips the REST API. The spike showed the CLI covers the lookup, step states, and logs, and it removes three problems the raw API had:

- **No numeric repo IDs.** Commands take `owner/name`.
- **No log decoding.** `pipeline log show` prints decoded text.
- **No token handling in the plugin.** Auth lives in the CLI's saved login.

Cost: the CLI must be installed per machine and set up once per server. The plugin checks for it and says how to get it.

## What the spike observed

All of this ran inside Claude Code's command sandbox, against Woodpecker 3.19.0 with CLI 3.19.0.

### Install

A `mise.toml` pin works and installs in about two seconds:

```toml
[tools]
"aqua:woodpecker-ci/woodpecker/woodpecker-cli" = "3.19.0"
```

mise has no short name for it. The aqua backend lists 3.17.0 through 3.19.0 and verifies a sha256 checksum. Homebrew offers only the current version, so mise is the better route when the CLI should match the server.

### Auth

`woodpecker-cli setup --server <url>` opens a browser page that hands a token back to the CLI over `http://localhost:<port>`. It saves a context file and stores the token in the OS keyring.

- **Run it outside the sandbox.** Keyring writes are blocked inside it. After setup, reads work fine inside the sandbox.
- **Use Chrome for the browser step.** Safari blocks the page's request to `http://localhost` as mixed content. Alternatively copy a personal access token from the user profile in the web UI and pass `--token`.
- **Setup is once per machine per server.**

### Running under the sandbox

Two settings are needed:

- **Disable the update check:** `WOODPECKER_DISABLE_UPDATE_CHECK=true`. The CLI otherwise calls `woodpecker-ci.org`, which the sandbox denies.
- **Allow the server host** in the sandbox's network allowlist.

The CLI creates its config directory at startup and exits with a fatal error if it can't. That already exists after `setup`, so it only bites before the first setup.

### Commands that worked

`<repo>` is `owner/name`. Failed pipelines exit 0, so status must be read from the output.

| Need | Command |
|------|---------|
| Compact list, newest first | `pipeline ls <repo> --limit N --output 'go-format={{.Number}} {{.Status}} {{.Commit}} {{.Branch}}'` |
| Only failures | add `--status failure` |
| Step states | `pipeline ps <repo> <n> --format '{{.workflow.Name}}/{{.step.Name}}={{.step.State}}'` |
| Failed step's log | `pipeline log show <repo> <n> <step-name>` |

Details that cost time to find:

- **Template keys on `ps` are lowercase** (`.workflow`, `.step`). `{{.Step.Name}}` prints `<no value>`. `pipeline ls` uses Go struct names (`.Number`, `.Commit`).
- **The default table prints the whole commit message** in one column, multi-line. Use `go-format` for anything a script reads.
- **Logs contain ANSI color codes** (43 of 77 lines in the sample). Strip them before showing or parsing.
- **Status strings seen:** `success`, `failure`, `running`, `killed`.

One real pipeline served as the first check: a failed `test-web` step whose log showed a flaky frontend test, the same failure already recorded in taskwarrior as `963c8abd-d16f-47fb-9887-d7fd153b94e1`.

### What the CLI doesn't do

- No lookup by commit SHA. Scan `pipeline ls` output and match `.Commit`.
- No JSON output on these commands (Go templates only).
- No "failed steps only" flag and no log tail. The helper does both.

## Open items from the spike

- **Gaps in pipeline numbers.** One repo's latest pipeline is number 91, but `pipeline ls --limit 200` returned 80. All 11 omitted numbers (6, 8, 18, 21, 26, 31, 34, 44, 53, 61, 83) return 404 from `pipeline show`, so the list looks complete and those numbers no longer exist. Why they vanished (deleted, purged by retention, or numbers consumed by something else) is unknown, and it was checked on one repo only.
- **Other status strings.** `pending`, `blocked`, `error`, `skipped`, and `declined` are expected but unseen.
- **Multiple servers.** The CLI keeps named contexts, but how a command picks one, and how that interacts with `--server`, is unverified.
- **Exit codes for errors.** An unconfigured CLI exited 1. Others are unchecked.
- **`lint` and `exec`** are documented but not tried.

## Goals

1. **Failed pipeline to log tail, with no human in the loop.** Start from a PR, a SHA, or a branch. End with the first failing step and the end of its log. Model the skill on `github-actions:investigating-runs`.
2. **Report the pipeline's actual state**, which has more than two values (see [States](#states)).
3. **Zero plugin config.** The server comes from the CLI's saved context. The repo comes from the git remote.
4. **Validate before pushing.** The authoring skill uses `woodpecker-cli lint`, and `exec` where Docker is available.
5. **A short authoring reference** for `.woodpecker.yml`, limited to facts true on any Woodpecker server.

## Non-goals

- **Server operations.** Restarting the server or fixing a dead webhook tunnel belongs in the runbook for the specific deployment.
- **Triggering, restarting, or editing secrets.** Nothing in the author's history asked for these.
- **House style.** Push-only triggers, Docker Hub images, and where files live are conventions of the author's repos. They go in those repos' own CLAUDE.md.
- **Token management.** The CLI owns it.

## What is generic and what is not

| Layer | Examples | Where it lives |
|-------|----------|----------------|
| Woodpecker itself | CLI commands, pipeline states, `failure: ignore`, step logs, shell and workspace behavior | The plugin |
| Forge-specific | Finding a PR's head SHA with `gh`, the `ci/woodpecker/push/woodpecker` status context | A thin optional adapter |
| Deployment | Hostname, tunnel, saved login, concurrency limits | The user's machine and runbook |
| House style | Trigger rules, base images, test conventions | The user's own repos |

With the CLI, the GitHub coupling shrinks to one step: turning a PR into a head SHA. Everything after that goes through Woodpecker's own commands.

## States

The helper returns exactly one of these, because pass and fail aren't where the lookup goes wrong.

| State | Meaning | Notes |
|-------|---------|-------|
| passed | All steps succeeded | Warn if a `failure: ignore` step failed |
| failed | A step failed | Report the **first** failing step, since later ones are skipped |
| running | In progress | Logs are partial, don't present them as the answer |
| queued | Waiting for an agent | Normal when the agent's concurrency limit is low |
| blocked | Waiting for manual approval | Common for pull requests from forks |
| no pipeline | Nothing ran for this SHA | Never read as passing. Likely causes: webhook not delivered, repo not activated, event filtered out by `when:`, or an old pipeline removed from the server |
| unreachable | Server down or network denied | Distinguish a sandbox network deny from a dead server, and don't blame the code |
| not set up | CLI missing or no saved login | Say which, and give the install or `setup` step |

## Failure modes in the lookup

- **Restarts.** A restart creates a new pipeline number for the same SHA. Take the latest.
- **PR lookups.** If a repo triggers on push only, pipelines have event `push` and no PR number. Resolve the PR's head SHA first.
- **Multiple workflows.** A `.woodpecker/` directory produces one workflow per file, and `ps` lists them all.
- **Cascades.** One failed step makes later steps skipped. Report the first failure.
- **Ignored failures.** A step with `failure: ignore` can fail while the pipeline passes.
- **Service containers.** A failed database service or a wait-loop timeout reads like a test failure.
- **Partial logs on running pipelines.**
- **Version drift.** CLI and server minor versions can differ. Pin the CLI to the server's version where possible.

## Environment surprises worth documenting

These look like code bugs and aren't. They are the real content of the authoring reference:

- Step commands run under `sh` (dash on Debian images), not bash.
- Cloned files are owned by root and steps run as root, so tests that depend on file permissions behave differently than locally.
- Services are reached by their service name as a hostname, not `localhost`.

## Skill shape

Modeled on the `github-actions` plugin, which pairs a Python helper (`gha-snapshot`, with fixture-based tests) with a skill and a `references/` directory.

- **Helper script does the mechanical work.** It shells out to the CLI, resolves the repo, finds the pipeline for a SHA, classifies the [state](#states), strips ANSI, and tails the first failing step's log. Invoke it through its interpreter (`uv run ...`), since plugin packaging can strip executable bits.
- **Skill covers the judgment.** What a state means, what to try next, when to stop and ask. The state names are a required field in the helper's output, so the model has a slot to fill and nothing to talk itself out of.
- **Two skills, prefixed with the plugin name** (skill names are global across installed plugins): `woodpecker-investigating-pipelines` and `woodpecker-authoring-pipelines`.
- **Descriptions list triggers only**, with no summary of the workflow, so the model reads the body instead of following the description. Trigger phrases: "Pipeline failed", `ci/woodpecker/...` status contexts, `.woodpecker.yml`, Woodpecker pipeline URLs of the form `/repos/<id>/pipeline/<n>`.
- **Name the skill in always-loaded context.** This repo's CLAUDE.md records that skills wrapping a tool Claude already half-knows can sit near zero recall on description alone. Ship a pointer in the plugin README and in whatever CLAUDE.md snippet the plugin recommends.
- **Keep SKILL.md short.** Authoring facts and per-state details go under `references/`.
- **Setup guidance lives in the skill's "not set up" state**: the `mise.toml` line, the `setup` command, the two sandbox settings.

## Testing

Each skill gets a baseline before it gets a body.

1. **Baseline first.** Run the failure scenarios with no skill and record what the model does. A real case exists: a red pipeline where Claude only saw "Pipeline failed" and the log had to be pasted in by hand.
2. **Fixture-driven scenarios, because a live server isn't repeatable.** Save CLI output for each state. The helper's tests run against these. Skill scenarios hand the model a fixture and check it reports the right state. The spike's real outputs (a failed list, a `ps` listing, a log with ANSI codes) are the first fixtures.
3. **Pressure on the "no pipeline" state.** The temptation is to read "no failing checks" as "passing". Test that one specifically, with a no-skill control, 5+ repetitions each, reading every output by hand.
4. **Shape the guidance to the failure.** A missing state is solved by the required output field. Wrong output shape is solved by stating what the output contains. Prohibition lists are for the case where the model knows the rule and skips it.
5. **Trigger evals last.** About 20 realistic prompts, half of them near-misses (a failing GitHub Actions run, a Buildkite build, a local test failure), then tune the description. See `plugins/buildkite/skills/investigating-builds/evals/` for the existing format.

## Next steps

1. **Confirm the list is complete** on a second repo, and find out why numbers disappear. If pipelines are purged by retention, an old SHA legitimately has no pipeline, and the "no pipeline" state should say that as a possible cause.
2. **Capture fixtures** for the states the spike saw, and find or provoke the ones it didn't (queued, blocked, no pipeline).
3. **Run the baseline** with no skill against those fixtures.
4. **Write the helper**, then the skill body, then trigger evals.
