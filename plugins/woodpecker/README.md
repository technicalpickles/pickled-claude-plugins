# woodpecker

Plugin for working with [Woodpecker CI](https://woodpecker-ci.org): find out why a pipeline failed, and write `.woodpecker.yml` that works the first time. Modeled on the `github-actions` plugin.

## Skills

- **woodpecker-investigating-pipelines**: load when a Woodpecker pipeline failed, is running, or never started.
- **woodpecker-authoring-pipelines**: load when writing, porting or validating a `.woodpecker.yml`.

## Helper

- **`woodpecker-snapshot`**: Python script (stdlib only) that drives `woodpecker-cli` to print one block: the pipeline's state, each step's state, and the first failed step's log tail. The first line is always `State: <state>`, one of passed, failed, running, queued, blocked, no pipeline, unreachable, unauthorized, not set up, or unknown. It also lists other pipelines for the same commit (a push and a `pull_request` run share one), and for a pipeline that failed before any step, the errors the server recorded. Invoked from the skill with `bash "${CLAUDE_PLUGIN_ROOT}/scripts/woodpecker-snapshot"`.

## Tool routes

A declarative route in `tool-routes.yaml` blocks `WebFetch` on Woodpecker pipeline URLs (`/repos/<id>/pipeline/<n>`, any host) and points at the investigating skill. Routes only fire if the [tool-routing](../tool-routing/README.md) plugin is installed.

## Setup

One-time per machine per Woodpecker server.

1. **Install the CLI, matching the server's version** (`curl -s https://<server>/version`), by whatever method fits your machine: a package manager, a release binary from the Woodpecker releases page, or a version manager.

2. **Log in** from your own terminal (it stores the token in the OS credential store where there is one, which a command sandbox can block):

   ```bash
   woodpecker-cli setup --server https://<your-server>
   ```

   The auth page hands the token back over `http://localhost:<port>`, which some browsers (Safari, for one) block as mixed content. Try another browser. Without a browser, create a personal access token in the web UI and pass it with `--token`; read it silently so it stays out of shell history (`read -rsp`, then `unset`).

3. **If you run Claude Code's command sandbox,** allow the server's host in its network allowlist.

## Requirements

- `woodpecker-cli`, logged in once with `woodpecker-cli setup`. See [the setup guide](skills/woodpecker-investigating-pipelines/references/setup.md).
- Python 3.9+
- `gh`, only for `--pr`

The plugin keeps no config of its own. The server comes from the CLI's saved login, and the repo from the git remote.

## Hooks

Skills that wrap a tool Claude already half-knows can go unused on description alone, so one hook script (`hooks/woodpecker-pointer.sh`) points Claude at both skills:

- **SessionStart**, when the working directory or one above it has `.woodpecker.yml`, `.woodpecker.yaml` or `.woodpecker/`.
- **PostToolUse**, once per session, the first time a `Bash`, `Read`, `Edit` or `Write` call's input or output mentions Woodpecker (`.woodpecker.yml`, `ci/woodpecker/...`, `woodpecker-cli`, or a `/repos/<id>/pipeline/<n>` URL). This catches sessions that work on a Woodpecker repo from another directory. It stays silent where SessionStart already pointed.

Measurements are in [the evals README](skills/woodpecker-investigating-pipelines/evals/README.md).

## Tests

```bash
cd plugins/woodpecker && uv run pytest
bats hooks/tests/
```

The snapshot tests use synthetic fixtures with a fake CLI runner and the hook tests feed it hook payloads, so neither needs a server.

## Not covered

- Triggering or restarting pipelines, managing secrets, and server operations
- More than one Woodpecker server (the CLI has named contexts; selecting between them is untested)
- Behavior evals for the skill bodies (see the [design doc](../../docs/specs/2026-10-17-woodpecker-plugin-design.md))
