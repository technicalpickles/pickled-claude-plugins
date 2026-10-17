#!/usr/bin/env bash
# Run a second-brain eval case inside the capture-evals VM (see ../README.md).
# Usage: [RUNS=n] [JOBS=n] run-in-vm.sh <case>
set -euo pipefail
export PATH="$HOME/.npm-global/bin:$HOME/.local/bin:$PATH"
cd "$(dirname "${BASH_SOURCE[0]}")/../../../.."  # repo root
claude plugin eval plugins/second-brain --case "${1:?case name}" --ablation none --scaffold --trust-plugin \
  --allow-tools Bash Write Edit Read Glob Grep --no-publish --runs "${RUNS:-1}" -j "${JOBS:-1}" --keep-temp --json "/tmp/${1:?case name}.json"
