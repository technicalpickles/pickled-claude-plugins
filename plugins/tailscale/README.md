# tailscale Plugin

Tailscale CLI reference and safe patterns for exposing local services over a tailnet.

## Skills

### tailscale-cli

Use when running `tailscale` commands to debug connectivity, inspect status, or manage `tailscale serve`/`funnel`/Services.

**Covers:**
- Where the `tailscale` binary lives (macOS GUI app vs. Homebrew vs. Linux) and why `which tailscale` can come up empty even when Tailscale is running
- `sudo`/operator gotchas — most `tailscale` commands don't need root
- Node-level `serve` vs. named Services (`svc:`) — separate config, separate status output
- The reliable order for standing up a brand-new Service (admin console → serve → `tailscaled` restart → approve → validate)
- Why `tailscale ping` fails against Service virtual IPs, and why self-curling a Service from its own serving host can hang

### tailscale-serve-patterns

Use when deciding how to expose a locally-running server over a tailnet, working with Tailscale identity headers for browser auth, or when a "bind is loopback" check doesn't reflect real exposure.

**Covers:**
- Loopback bind + `tailscale serve` proxy (safe default) vs. binding directly to the tailnet interface (unauthenticated, exposure-widening)
- The IPv4 (`127.0.0.1`) vs. IPv6 (`[::1]`) loopback trap
- Empirically-verified behavior of Tailscale identity headers on Services (undocumented by Tailscale itself): Serve overwrites spoofed headers rather than stripping them, but a request straight to the loopback port arrives unverified — making loopback-only binding a security invariant, not just hygiene
- Why tagged devices and Funnel traffic never carry identity headers, and why that fallback isn't optional
- Why an automated "bind is loopback" check can pass while a Docker `-p` publish or reverse proxy still exposes the port

## Installation

Requires the [pickled-claude-plugins marketplace](../../README.md#installation). Then:

```
/plugin install tailscale@pickled-claude-plugins
```
