#!/usr/bin/env bash
set -euo pipefail
git init -q .
git config user.email eval@example.com
git config user.name eval

mkdir -p rates docs/adr

cat > rates/lookup.py <<'EOF'
import json
import urllib.request

UPSTREAM = "https://fx-upstream.example/v1/rate"


def get_rate(base, quote):
    """Fetch a single FX rate from upstream. Called on every invoice render."""
    with urllib.request.urlopen(f"{UPSTREAM}?base={base}&quote={quote}", timeout=5) as r:
        return json.load(r)["rate"]
EOF

cat > docs/adr/0003-deploy-topology.md <<'EOF'
# ADR 0003: Deploy topology for the rates service

Status: accepted

The rates service runs as 12 replicas behind the load balancer, autoscaling
between 6 and 40 on CPU. Replicas are recycled on every deploy (several times
a day), so anything held in process memory lives for at most a few hours.
EOF

cat > docs/adr/0007-shared-cache-for-rates.md <<'EOF'
# ADR 0007: No in-process caching of FX rates

Status: accepted

## Context

In the Q2 incident (two replicas quoting different EUR rates for the same
invoice for ~40 minutes) we had an in-process LRU on each replica. Because
each replica warmed independently, invoices rendered on different replicas
disagreed, and finance had to reissue 312 invoices.

## Decision

FX rates must come from a single shared source of truth per minute. Any cache
must be shared across replicas (we already run a managed Redis for sessions,
`cache-shared-01`, which the platform team said we can use). In-process caches
are not allowed for anything that ends up on an invoice.

## Consequences

One extra network hop (~1ms p50) per lookup. Rates go stale for at most the
TTL, which must be <= 60s per finance.
EOF

cat > README.md <<'EOF'
# rates service

Serves FX rates to invoice rendering. See docs/adr/ for design decisions.
EOF

git add -A && git commit -qm "rates service skeleton + ADRs"
