# Services (`svc:`) vs. node-level `serve`

Two different Tailscale features look similar but have separate config and separate status output:

- **Node-level serve**: `tailscale serve --https=443 http://127.0.0.1:8080` — attaches to *this node's* own identity (`<hostname>.<tailnet>.ts.net`).
- **Services**: `tailscale serve --service=svc:myapp --https=443 http://127.0.0.1:8080` — proxies for a named **Service** with its own virtual IP/hostname (`myapp.<tailnet>.ts.net`), independent of which node is currently serving it (enables failover/migration later).

## The gotcha that eats debugging time

`tailscale serve status` **with no flags only shows node-level routes.** A Service's config is invisible to it — it prints `No serve config` even when the Service is fully configured and traffic is flowing. This looks exactly like "the serve command silently failed" and will send you down a rabbit hole of restarting `tailscaled`, running `tailscale down`/`up`, and re-issuing the serve command, all for nothing.

**Fix:** always check `tailscale serve status --json` and look under `.Services["svc:<name>"]`. That's the real source of truth for Service-based proxies.

```bash
tailscale serve status --json | jq '.Services'
```

## Prerequisite gotcha

`tailscale serve --service=svc:X ...` does **not** create the Service. A Service must already be defined in the tailnet admin console (Services page, name + port) before the CLI has anything to attach a pending-host-approval to. Running the serve command against an undefined Service reports success ("Serve started and running in the background") but nothing ever shows up as pending, and the hostname never resolves to anything real. Define the Service first, then run `serve --service=`.
