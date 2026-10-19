# Setting up woodpecker-cli

One-time per machine per Woodpecker server. Everything below was run against Woodpecker 3.19.0.

## 1. Install, pinned to the server version

Check what the server runs, since the CLI should match it:

```bash
curl -s https://<your-server>/version
```

Then pin it in `mise.toml`:

```toml
[tools]
"aqua:woodpecker-ci/woodpecker/woodpecker-cli" = "3.19.0"
```

`woodpecker-snapshot` finds the CLI on its own: it uses `PATH` if the CLI is there, otherwise the newest copy under `~/.local/share/mise/installs/` (or `$MISE_DATA_DIR`). Agent shells often lack mise's shims, so this matters. If neither exists it prints `State: not set up`. When calling `woodpecker-cli` directly, use `mise exec -- woodpecker-cli ...` or that installs path.

mise has no short name for this tool, so use the full aqua name. The aqua backend verifies a sha256 checksum. `brew install woodpecker-cli` also works but only offers the current release.

## 2. Log in (outside the command sandbox)

```bash
woodpecker-cli setup --server https://<your-server>
```

This saves a context file and puts the token in the macOS Keychain. Keychain writes are blocked inside the command sandbox, so the user runs this in their own terminal.

- **Browser step:** the auth page hands the token back to the CLI over `http://localhost:<port>`. Safari blocks that as mixed content. Use Chrome or Firefox (set one as the default browser, or paste the `/cli/auth?port=...` URL into it while the CLI waits).
- **Without a browser:** copy a personal access token from the user profile in the web UI and pass it with `--token`. Read it silently so it stays out of shell history:

```bash
read -s -P "token: " WP_TOKEN; and woodpecker-cli setup --server https://<your-server> --token $WP_TOKEN; set -e WP_TOKEN
```

(That line is fish syntax. In bash use `read -rsp` and `unset`.)

After setup, reading the saved login works fine inside the sandbox.

## 3. Sandbox settings

- **Allow the server's host** in the sandbox's network allowlist. Without it the CLI reports a bare `Forbidden`, and the snapshot shows `State: unreachable` with this fix.
- **`WOODPECKER_DISABLE_UPDATE_CHECK=true`** is set by the snapshot helper. If you call the CLI directly, set it yourself, or the update check (a call to woodpecker-ci.org) fails under the sandbox.
- **The config directory must already exist.** The CLI creates it at startup and exits with a fatal error if it can't. `setup` creates it, so this only matters before the first setup.

## Not covered

Several servers at once. The CLI keeps named contexts, but how a command picks one, and how that interacts with `--server`, hasn't been tested.
