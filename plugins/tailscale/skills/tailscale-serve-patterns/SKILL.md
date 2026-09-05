---
name: tailscale-serve-patterns
description: Use when deciding how to expose a locally-running server over a tailnet (loopback bind + `tailscale serve` vs. binding directly to the tailnet interface), when a service is reachable at its Tailscale address but a request seems to bypass expected auth, when working with Tailscale identity headers (`Tailscale-User-Login` and friends) for browser auth, or when a "bind is loopback-only" security check doesn't seem to reflect what's actually reachable (Docker port publish, reverse proxy, container networking).
---

# Tailscale Serve Patterns

## Overview

Two ways to make a local service reachable over a tailnet, with very different security properties: bind loopback-only and let `tailscale serve` proxy HTTPS in front of it, or bind the process directly to the tailnet interface address. For CLI mechanics (commands, Services vs. node-serve, troubleshooting `serve status`), see the `tailscale-cli` skill instead — this skill is about which exposure shape to choose and what it implies for auth.

## The two binding patterns

| | Loopback bind + `tailscale serve` | Direct bind to tailnet interface |
|---|---|---|
| What's exposed | `127.0.0.1:<port>` only; `serve` proxies HTTPS at `<host>.<tailnet>.ts.net` | Plain HTTP directly at the tailnet IP (e.g. `100.x.y.z:<port>`) |
| Auth | Tailscale itself is the gate — only tailnet members can reach the hostname at all; TLS terminated by `tailscaled` | None unless the app adds its own — anyone on the tailnet who knows the IP:port can hit it over unencrypted HTTP |
| Setup cost | One extra `tailscale serve` mapping to create/tear down | Zero extra config — just bind a different address |
| Failure mode if misconfigured | Hitting `<tailnet-hostname>:<port>` directly (skipping the proxy) fails, because the app only bound loopback — this is *expected*, not a bug | A stray bind flag or default (`0.0.0.0` instead of `127.0.0.1`) silently widens exposure to the whole tailnet with no signal |

**Default to loopback + `serve`.** It's the pattern used across this project's homelab services (bind `127.0.0.1:<port>`, expose via host `tailscaled` + Services) and what the `crit` review tool's own auto-mode classifier treats as the expected, low-friction path. Direct tailnet-interface binding is the exception, appropriate for short-lived single-user sessions (e.g. "review this on my phone for the next ten minutes, I'm the only one on this tailnet") — treat it as something that needs an explicit, conscious opt-in (a flag like `--allow-unauthenticated-network`), not a default.

`serve` does not change what the process itself binds to — it's a separate proxy layer. If a server only binds `127.0.0.1`, requests straight to the tailnet hostname's port will fail; you must go through the URL/port `serve` publishes (usually 443), not the app's own port.

## The IPv4/IPv6 loopback trap

`127.0.0.1` and `[::1]` are both "loopback" but not interchangeable. A listener bound to `[::1]` only (IPv6 loopback) is unreachable from `127.0.0.1` (IPv4) — and unreachable from Tailscale either way, since Tailscale doesn't change this. If a browser's `localhost` resolves to IPv4 first and the server only listens on `[::1]`, you'll see a connection failure that looks tailnet-related but has nothing to do with Tailscale at all. Check `lsof -i` for the actual bound address before assuming a tailnet/proxy problem.

## Identity headers: what's actually verified, not assumed

Tailscale Serve/Services can stamp identity headers (`Tailscale-User-Login`, `Tailscale-User-Name`, `Tailscale-User-Profile-Pic`) onto proxied requests, which is tempting to use as a browser auth signal instead of a shared secret. **Tailscale's own docs describe this for node-level `serve` but say nothing about `--service=svc:` Services** — if your deployment uses Services (see `tailscale-cli`), don't assume the docs cover your case. Verify empirically instead of trusting the docs or your assumptions:

- **Services do stamp the headers** (confirmed by temporarily adding a test path handler to a live service and reading what arrived).
- **A spoofed header sent *through* Serve is overwritten, not merely stripped** — Serve replaces `Tailscale-User-Login` with the real caller's identity even if the client tried to set its own value.
- **The same spoofed header sent straight to the loopback port arrives verbatim.** This is the load-bearing fact: identity-header trust is only safe if the loopback bind is the *only* path to the backend. Anything that can reach the port directly (a misconfigured `0.0.0.0` bind, a container publishing the port beyond loopback) can forge any identity. The loopback-only bind stops being just network hygiene and becomes a security invariant the moment you trust these headers.
- **Tagged devices (servers, CI runners, agents) get zero identity headers**, even through Services. A machine-to-machine caller has no identity path, ever — it needs its own credential (API key), and that requirement doesn't go away just because identity headers exist for humans.
- **Funnel traffic carries no identity headers either.** If a route can also be reached via Funnel, header-based auth silently degrades to no-auth-signal on that path — the request needs a fallback (e.g. an API key check) rather than assuming the header will be present.

If you're building header-based auth: default the trust flag off, fail closed (empty allow-list = reject, don't accept-any-identity), and fail fast at startup if the flag is on with no allow-list configured — a silently-useless config (flag on, empty allow-list) just re-prompts users with no explanation of why.

## Automated "is this bound to loopback" checks can lie

A security/doctor check that inspects `gateway.bind` (or equivalent app-level config) and calls it safe because it says `127.0.0.1` has no visibility into what's *actually* reachable: Docker's `-p` publish flag can expose a container's "loopback" port to the whole host or network regardless of what the app thinks it bound to, and a reverse proxy or `tailscale serve` mapping sits entirely outside the app's own config. A green check here means "the app's own bind setting is loopback," not "this is only reachable from this machine." Verify actual reachability from a different tailnet node (`curl` the tailnet hostname, or attempt the raw port) rather than trusting a config-level check alone.

## Common mistakes

| Mistake | Why it's wrong |
|---|---|
| Trusting `Tailscale-User-*` headers without confirming Services (not just node-serve) actually stamp them for your setup | Undocumented by Tailscale for Services; verify empirically first |
| Building identity-header auth without a fallback for tagged devices or Funnel traffic | Both produce zero identity headers by design — the fallback path isn't optional |
| Assuming a `0.0.0.0`/tailnet-interface bind flag is fine because "only I'm on this tailnet" | True today, but it's an unauthenticated-by-default state with no expiry — treat it as an explicit, temporary opt-in, not a config to leave on |
| Debugging a `[::1]`-vs-`127.0.0.1` connection failure as a Tailscale problem | Check the actual bound address first; it may have nothing to do with the tailnet at all |
| Trusting a passing "bind is loopback" doctor/security check as proof of true exposure | It only sees the app's own config, not Docker publish or reverse-proxy layers in front of it |
