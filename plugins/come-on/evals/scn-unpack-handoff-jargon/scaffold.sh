#!/usr/bin/env bash
set -euo pipefail
mkdir notes
printf 'run-b: blocked on auth step (see #456). grp-7: 4 flaky tasks, rerun pending.\nt0 baseline still valid. Need call: fix run-b first or rerun grp-7?\n' > notes/status.md
