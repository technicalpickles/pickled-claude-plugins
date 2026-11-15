# Datadog probes

Two ways to reach Datadog from a probe. Prefer `pup` if it's installed and
authenticated — it's a direct CLI, no bridge needed. Fall back to `mcporter`
(via an MCP server) if `pup` isn't available.

## Primary: `pup`, the Datadog CLI

Verified 2026-08-28: `pup` 0.63.0 is installed and OAuth-authenticated on this
machine (`pup auth status` → `Authenticated for site: datadoghq.com`, has a
refresh token). This machine also has a whole `pup:dd-*` skill family for
Datadog work, which is a strong signal `pup` is the intended tool here, not
an edge case.

    pup metrics query --query='<dd query>' --from='5m' --to='now'

Real output, live-verified:

```json
{
  "status": "success",
  "data": {
    "series": [
      {
        "metric": "system.cpu.user",
        "pointlist": [[1787928110000.0, 9.63], [1787928115000.0, 9.56], ...]
      }
    ]
  }
}
```

`pointlist` is `[[timestamp, value], ...]`, one entry per rollup interval —
same shape as the `mcporter` path below, so the same caveat applies: `length`
counts buckets, not hits (see "The flag-ramp case").

**Caveat:** the OAuth token has a short TTL (41 minutes left when checked
today) but `has_refresh: true` — it should refresh silently on the next call
rather than requiring `pup auth login` again, but hasn't been confirmed
end-to-end across a refresh boundary. If a long-running watch's probe
suddenly starts failing after running fine for a while, check `pup auth
status` first before assuming the Datadog query itself broke.

## Fallback: `mcporter` (MCP bridge)

If `pup` isn't installed or isn't authenticated, and a Datadog MCP server is
configured, `mcporter` reaches it the same way it reaches any other MCP tool
— no separate setup needed.

Verified 2026-08-28: `mcporter` 0.13.7 (mise shim, Node 24) reads MCP server
definitions straight from `~/.claude.json`, and **reuses Claude Code's existing
OAuth tokens** — a live call against a currently-healthy OAuth'd HTTP MCP server
returned real data, exit 0, sandboxed, with no `mcporter auth` step. Roughly
16-20 of the configured servers are healthy at any given moment; individual
HTTP MCP servers go in and out of availability over the course of a day
(ordinary flakiness, not an auth or bridge problem).

So there is no per-server auth dance. If a server works in Claude Code, it
works from the shell — you just need to pick one that's actually up right now.

Sanity-check the bridge with any currently-healthy read-only tool. `mcporter`
exposes no read/write annotation — judge from the verb in the tool's name and
its docstring (`get-`/`list-`/`who-am-i`/`search-` read; `create-`/`set-`/
`revoke-`/`update-` write), and skip anything ambiguous:

    mcporter list                       # see what's healthy right now
    mcporter call <healthy-server>.<a-read-only-tool>   # e.g. a who-am-i, list-*, or get-* tool

If your first-choice server times out or errors, that's the server, not the
bridge — pick a different healthy one from `mcporter list` and retry.

**As of 2026-08-28, no Datadog MCP server is configured on this machine**
(`mcporter list | grep -i datadog` returns nothing) — moot while `pup` works,
but if `pup` ever stops being the answer, this is the gap to close:

    mcporter list <dd-server> --brief          # find the query tool
    mcporter call <dd-server>.<tool> ...       # confirm it returns data, exit 0

Probe shape once a server exists:

    mcporter call <dd-server>.<query-tool> query='<dd query>' from='-5m' \
      | jq -r '<extract a single scalar>'

Wrap it in the loop as usual:

    watch-loop.sh --label 'checkout-v2 flag hits' --interval 60 \
      --probe "mcporter call <dd-server>.<query-tool> query='...' | jq -r '...'"

## The flag-ramp case

The case this skill was built for: a flag was ramped to 5% and the user wants
the first request. Probe a count, not a boolean — a count tells you *how many*,
which is more useful than "yes".

Be careful what you're counting. `pointlist | length` counts time buckets in
the query window, not hits — it plateaus once the window fills in, regardless
of traffic, so it does NOT "keep reporting as traffic grows" the way a raw hit
count would. For an actual growing count, sum the values instead:

    pup metrics query --query='<dd query>' --from='5m' --to='now' \
      | jq -r '"hits=\(.data.series[0].pointlist | map(.[1]) | add // 0)"'

(via `mcporter`, same fix: `.series[0].pointlist | map(.[1]) | add` instead of
`length` — note `mcporter`'s response isn't nested under `.data` the way
`pup`'s is, so drop that prefix for that path.)

The exact right shape still depends on the metric type (a count metric sums
meaningfully; a gauge/rate does not) and the specific query — the mechanism
above is live-verified against a real metric (`system.cpu.user`), but no
specific "GraphQL hits for flag X" query has been tested end-to-end, since
that depends on which flag and which service. Verify the actual query against
real data before trusting it unattended.

Use `--once` if they only care about the first hit. Use `Monitor` without
`--once`, `timeout_ms` at the max and re-armed on each expiry, if they want
every subsequent one.

## Notes

- Interval 60s or more. Datadog's API is rate-limited and metric data is
  usually delayed anyway, so faster polling buys nothing.
