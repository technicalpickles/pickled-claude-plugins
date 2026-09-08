# Setting up a brand-new Service (the reliable order)

Getting the order wrong is the single most common source of "why won't this approve" on a first deploy. Follow it in this order, not the order a deploy script's automated steps happen to run in:

1. **Define the Service in the admin console first**, before running anything else: `https://login.tailscale.com/admin/services` → "Define Service" → name + port. A `tailscale serve --service=` call against an undefined Service can report success with nothing to actually show for it.
2. **Run `tailscale serve --service=svc:X --https=443 <target>`** on the host that will proxy it.
3. **Restart `tailscaled` on that host**: `sudo systemctl restart tailscaled` (Linux). Confirmed required, not optional — until the daemon restarts, the pending-proxy registration from step 2 does not get pushed up to Tailscale's Services backend, and nothing shows up as approvable in step 4. Just re-toggling `serve ... off` / `serve ... on` is **not** a substitute for this restart.
4. **Approve the pending host** in the admin console (Services page, next to the Service you defined in step 1).
5. **Validate** from a different node: `curl -fsS https://<name>.<tailnet>.ts.net/<health-path>` (never from the serving host itself — self-curl from the serving host can hang, see the troubleshooting checklist in SKILL.md).

This restart is a deliberate, expected part of standing up a new Service — it's a different situation from the "don't restart tailscaled reflexively" troubleshooting advice in SKILL.md, which is about an *already-working* Service whose `serve status` output merely looks wrong.

**Restarting `tailscaled` on a shared host is a real action, not a diagnostic one** — it affects connectivity for every service that host proxies. Don't do it reflexively while chasing a status-display confusion on an *already-working* Service; confirm with whoever owns the host first, and reach for it only after ruling out the display gotchas in SKILL.md. (This is different from standing up a brand-new Service, where the restart is an expected, required step — see above.)
