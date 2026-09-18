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

## The hosting node itself must be tagged

Separate from any `grants`/ACL reachability rule, `tailscale serve
--service=svc:X ...` requires the node running that command to be a tagged
node, full stop. An untagged node -- even one with perfectly normal
tailnet connectivity otherwise -- fails outright with:

```
service hosts must be tagged nodes
```

This isn't a permissions/grants problem to debug with `tailscale acl`-style
policy reasoning; it's a hard requirement on the hosting node's own tags.
If a node that was successfully hosting Services suddenly can't, and every
other symptom (SSH, ping, container health) looks fine, suspect the node
lost its tag rather than a Services-specific bug -- see the
`tailscale-cli` skill's `references/acls.md` ("A tag can also be lost from
an already-tagged, already-working node") for the confirmed trigger and
fix.
