# `tailscale ping` and self-curl gotchas

## `tailscale ping` doesn't work on Service virtual IPs

`tailscale ping <service-hostname-or-vip>` returns `no matching peer` even when the Service is healthy — a Service's virtual IP isn't a real WireGuard peer, so ping has nothing to reach. This is expected, not a failure signal. To test a Service, `curl` the HTTPS hostname instead:

```bash
curl -fsS --max-time 8 https://myapp.<tailnet>.ts.net/healthz -o /dev/null -w 'HTTP %{http_code}\n'
```

## Self-curl from the serving host can hang

Curling a Service's own hostname *from the same host that's proxying it* can time out or hang (hairpin/self-connect issue) even when the Service works fine for every other node. Don't conclude a Service is broken from a failed self-test on the host — verify from a different tailnet node (e.g. your Mac, or another peer) before troubleshooting further.
