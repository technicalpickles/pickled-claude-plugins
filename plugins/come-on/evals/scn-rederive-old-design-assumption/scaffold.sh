#!/usr/bin/env bash
set -euo pipefail
mkdir -p docs config
printf '# Export design (2026-05-02)\nAssumption: we run a single worker process, so one shared queue is fine.\n' > docs/design.md
printf 'concurrency: 8\nprocesses: 3   # scaled up 2026-09-14\n' > config/worker.yml
