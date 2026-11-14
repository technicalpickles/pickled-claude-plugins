# When woodpecker-cli isn't ready

For the `not set up`, `unauthorized` and `unreachable` states. The login and install are the user's steps, so show the printed fix and point them at the plugin README's setup section. Verified against Woodpecker 3.19.0.

## What the CLI needs

- **Installed.** The snapshot uses `PATH`, and as a last resort looks in a mise install dir (a convenience, not an assumption about how it was installed). If it reports the CLI missing, find out how this machine installs tools before suggesting a method; don't assume one. Agent shells often have a different `PATH` than the user's terminal.
- **Logged in.** `woodpecker-cli setup --server <url>` saves a context file and stores the token in the system keychain. Keychain writes are blocked inside a command sandbox, so the user runs it in their own terminal. Reading the saved login works fine in the sandbox afterwards.
- **A matching version.** The CLI should match the server (`curl -s https://<server>/version`).

## Under a command sandbox

- **Allow the server's host** in the network allowlist. Without it the CLI reports a bare `Forbidden`, and the snapshot shows `State: unreachable` with this fix.
- **`WOODPECKER_DISABLE_UPDATE_CHECK=true`** is set by the snapshot helper. If you call the CLI directly, set it yourself, or the update check (a call to woodpecker-ci.org) fails.
- **The config directory must already exist.** The CLI creates it at startup and exits with a fatal error if it can't. `setup` creates it, so this only matters before the first setup.

## Not covered

Several servers at once. The CLI keeps named contexts, but how a command picks one, and how that interacts with `--server`, hasn't been tested.
