# woodpecker

Plugin for working with [Woodpecker CI](https://woodpecker-ci.org): find out why a pipeline failed, and write `.woodpecker.yml` that works the first time. Modeled on the `github-actions` plugin.

## Skills

- **woodpecker-investigating-pipelines**: load when a Woodpecker pipeline failed, is running, or never started.
- **woodpecker-authoring-pipelines**: load when writing, porting or validating a `.woodpecker.yml`.

## Helper

- **`woodpecker-snapshot`**: Python script (stdlib only) that drives `woodpecker-cli` to print one block: the pipeline's state, each step's state, and the first failed step's log tail. The first line is always `State: <state>`, one of passed, failed, running, queued, blocked, no pipeline, unreachable, unauthorized, not set up, or unknown. Invoked from the skill with `bash "${CLAUDE_PLUGIN_ROOT}/scripts/woodpecker-snapshot"`.

## Tool routes

A declarative route in `tool-routes.yaml` blocks `WebFetch` on Woodpecker pipeline URLs (`/repos/<id>/pipeline/<n>`, any host) and points at the investigating skill. Routes only fire if the [tool-routing](../tool-routing/README.md) plugin is installed.

## Setup

One-time per machine per Woodpecker server.

1. **Install the CLI, pinned to the server's version** (`curl -s https://<server>/version`). With mise, use the full aqua name, since there's no short one:

   ```toml
   [tools]
   "aqua:woodpecker-ci/woodpecker/woodpecker-cli" = "<server version>"
   ```

   `brew install woodpecker-cli` also works but only offers the current release.

2. **Log in** from your own terminal (it writes the system keychain, which a command sandbox blocks):

   ```bash
   woodpecker-cli setup --server https://<your-server>
   ```

   The auth page hands the token back over `http://localhost:<port>`, which Safari blocks as mixed content. Use Chrome or Firefox. Without a browser, create a personal access token in the web UI and pass it with `--token`; read it silently so it stays out of shell history (`read -rsp`, then `unset`).

3. **If you run Claude Code's command sandbox,** allow the server's host in its network allowlist.

## Requirements

- `woodpecker-cli` (on `PATH`, or a mise install under `~/.local/share/mise/installs/`, which the snapshot finds by itself), logged in once with `woodpecker-cli setup`. See [the setup guide](skills/woodpecker-investigating-pipelines/references/setup.md).
- Python 3.9+
- `gh`, only for `--pr`

The plugin keeps no config of its own. The server comes from the CLI's saved login, and the repo from the git remote.

## Recommended CLAUDE.md pointer

Skills that wrap a tool Claude already half-knows can go unused on description alone. Add a line like this to a project that builds with Woodpecker:

```markdown
CI is Woodpecker. To find out why a pipeline failed, use the woodpecker-investigating-pipelines skill.
```

## Tests

```bash
cd plugins/woodpecker && uv run pytest
```

Tests run against synthetic fixtures with a fake CLI runner, so they need no server.

## Not covered

- Triggering or restarting pipelines, managing secrets, and server operations
- More than one Woodpecker server (the CLI has named contexts; selecting between them is untested)
- Trigger-accuracy evals for the skill descriptions and behavior evals for the skill bodies (see the [design doc](../../docs/specs/2026-10-17-woodpecker-plugin-design.md))
