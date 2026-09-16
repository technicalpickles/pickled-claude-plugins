---
name: tailscale-cli
description: Use when running `tailscale` commands to debug connectivity, inspect status, or manage `tailscale serve`/`funnel`/Services — especially when `tailscale serve status` looks wrong, `tailscale` isn't found in a shell, `tailscale ping` fails against a host that's clearly up, you're working across a mix of macOS (GUI app) and Linux (VM/container) nodes in the same tailnet, or a node/sidecar joins fine but something downstream (a grant, an app-level check) crash-loops or silently fails — that's often an ACL/tagOwners issue, not a code bug. Also use for authoring or reading tailnet ACLs (tagOwners, grants, the legacy `acls` array) or querying the live policy via the Tailscale API.
---

# Tailscale CLI

## Overview

The `tailscale` CLI behaves differently depending on install shape (macOS GUI app vs. Linux package) and config model (plain node-level `serve` vs. `--service=svc:X` Services). Most "tailscale is broken" moments are actually one of these known gotchas, not a real outage.

For binding/exposure architecture (loopback vs. tailnet-interface binding, identity headers, auth implications) rather than CLI mechanics, see the `tailscale-serve-patterns` skill instead.

## Where the binary lives

| Environment | Binary | Notes |
|---|---|---|
| macOS, Tailscale.app (GUI) | `/Applications/Tailscale.app/Contents/MacOS/Tailscale` | **Not on `$PATH`** — the App Store/direct-download GUI app does not symlink a `tailscale` command by default. `which tailscale` returning nothing does not mean Tailscale isn't running; check the menu-bar icon or `/Applications/Tailscale.app/Contents/MacOS/Tailscale status` directly. Alias it if you use it often: `alias tailscale=/Applications/Tailscale.app/Contents/MacOS/Tailscale`. |
| macOS, Homebrew (`brew install tailscale`) | `tailscale` on `$PATH` | Different install path than the GUI app; if both are present they can diverge in version. |
| Linux (systemd package, VM/container) | `tailscale` on `$PATH`, daemon is `tailscaled` | Standard install. Talks to `tailscaled` over a local socket. |

**Diagnostic tell:** if a `... | jq ...` pipeline throws `jq: parse error: Invalid numeric literal at line 1, column N`, don't debug jq — the upstream command almost certainly failed (e.g. `command not found: tailscale`) and its error text got merged into stdout via `2>&1`, and jq is choking on that text, not real JSON. Re-run the upstream command alone first.

## Root/sudo: don't reach for it by default

`tailscale status` and `tailscale ping` are normally readable by any local user — no `sudo` needed. Mutating commands (`serve`, `funnel`, `up`/`down` in some configs) may need root, *or* may work passwordless if the local user is set as the tailscale operator (`tailscale set --operator=<user>`) or granted a scoped `NOPASSWD` sudo rule for `tailscale serve *`.

Symptom of getting this wrong: `sudo tailscale status --json` hangs asking for a password ("a terminal is required to read the password") on a host where plain `tailscale status` works fine and `sudo tailscale serve status` also works fine (because sudo is scoped to `serve *`, not `status`). Fix: drop the unneeded `sudo`, or check what the sudoers rule actually covers (`sudo -n -l`) before assuming Tailscale itself is broken.

## Services vs. node-level serve

Two different features that look similar but have separate config and status output — a Service's config is invisible to bare `tailscale serve status` (it prints `No serve config` even when fully configured), and a serve command against an undefined Service reports success but does nothing. Full explanation and the fix (`serve status --json`, `.Services`): [references/services.md](references/services.md).

## `serve ... off` removes the whole port's config, not just your mapping

`tailscale serve --https=443 off` (or the bare-port form) tears down **every** path mapping on that port, not just the one you added. Confirmed by running it on a node with two node-level mappings (`/` and `/readme-preview`) to remove only `/`: `serve status --json` came back completely empty afterward, both mappings gone. There's no scoped "remove just this path" for node-level serve — `tailscale serve --set-path=/some/path off` fails outright if that exact path isn't the one currently mapped, and even a successful narrower-looking command can still wipe the shared `:443` config underneath it.

If a node has more than one node-level mapping, or you're not sure whether it does: `tailscale serve status --json` before you touch anything, and after, so you know exactly what existed and can rebuild it (`tailscale serve --bg --set-path=<path> <target>` per mapping) rather than assuming your teardown was scoped to what you added. This matters most on a shared host, or anywhere state might have been added since you last checked — never assume you're the only thing that's touched `serve` on that node.

## ACLs: tagOwners, grants, and the silent-drop pattern

There's no local `tailscale acl` command — the policy file only lives in the admin console or the API. A node can join the tailnet fine while silently losing a requested tag it wasn't authorized for (`tagOwners`), which then breaks something downstream (a grant, an app-level check) without any Tailscale-level error. Recognizing this pattern, tagOwners vs. grants, legacy `acls` vs. current `grants`, and reading the live policy via the API: [references/acls.md](references/acls.md).

## Setting up a brand-new Service

Has a specific required order (define in admin console → `serve --service=` → restart `tailscaled` → approve → validate from a different node) that's easy to get wrong on a first deploy: [references/new-service-setup.md](references/new-service-setup.md).

## `ping` and self-curl gotchas

`tailscale ping` doesn't work against Service virtual IPs (`no matching peer` is expected, not a failure), and curling a Service's own hostname from the host that's proxying it can hang even when the Service is healthy for everyone else: [references/ping-and-curl-gotchas.md](references/ping-and-curl-gotchas.md).

## Quick troubleshooting checklist: "serve status looks wrong"

1. Are you checking `serve status` bare, or `--json`? Bare misses Services — always add `--json` for Services.
2. Did you `sudo` a command that doesn't need it (or that isn't covered by a scoped sudoers rule)? Try without `sudo` first.
3. Is the target a Service (`svc:`) and does it actually exist in the admin console yet? A serve command against an undefined Service "succeeds" but does nothing.
4. Are you testing with `ping` against a Service VIP? Use `curl` against the hostname instead.
5. Are you testing from the same host that's serving the proxy? Test from a different node.
6. Only after 1-5 are ruled out: check `tailscaled` itself (`systemctl status tailscaled`, `tailscale status`, node's `BackendState`).

**Restarting `tailscaled` on a shared host is a real action, not a diagnostic one** — it affects connectivity for every service that host proxies. Don't do it reflexively while chasing a status-display confusion on an *already-working* Service; confirm with whoever owns the host first, and reach for it only after ruling out the gotchas above. (Standing up a *new* Service is different — there the restart is an expected, required step: [references/new-service-setup.md](references/new-service-setup.md).)

## Useful commands

| Command | Purpose |
|---|---|
| `tailscale status` | Peer list + this node's connection state (no sudo needed normally) |
| `tailscale status --json` | Same, machine-readable — `.Self`, `.Peer[]`, `.CurrentTailnet`, `.Health` |
| `tailscale serve status --json` | Real Services + node-serve config — see [references/services.md](references/services.md) |
| `tailscale ping <peer>` | WireGuard-level reachability to a real node (not Services) |
| `tailscale version` | Compare versions across nodes when behavior differs between hosts |
| `tailscale serve --service=svc:X ... off` | Disable a Service's proxy config (keeps the Service definition) |
| `tailscale serve clear svc:X` | Remove all serve config for a Service |
