#!/usr/bin/env bash
# Diagnose `npx @techpickles/sb` failures. Run this ONLY after an actual sb call has
# failed - it is not a preflight check to run before every command.
#
# Historically skills ran `sb --version` (and friends) before every flow to guard
# against an npx bin-dispatch quirk where `npx @techpickles/sb --version` silently
# resolves to npm itself. That quirk hasn't reproduced in a long time, so the checks
# were pure overhead on the happy path. This script bundles the same diagnosis into
# one call for the rare case sb actually breaks.
set -uo pipefail

version_output=$(npx @techpickles/sb --version 2>&1)
sb_status=$?
npm_version=$(npm --version 2>&1)

if [[ $sb_status -ne 0 ]]; then
  echo "sb CLI is not available (npx exited $sb_status)."
  echo "Install Node.js and npm, then try again."
  echo "Or install globally for faster execution: npm i -g @techpickles/sb"
  exit 1
fi

if [[ "$version_output" == "$npm_version" ]]; then
  echo "npx is misdispatching 'sb' to npm itself (known npx bin-dispatch quirk)."
  sb_path=$(ls ~/.npm/_npx/*/node_modules/@techpickles/sb/dist/index.js 2>/dev/null | head -1)
  if [[ -n "$sb_path" ]]; then
    echo "Direct invocation available: node \"$sb_path\" <subcommand>"
  else
    echo "Could not locate a cached sb install under ~/.npm/_npx."
    echo "Try: npm i -g @techpickles/sb"
  fi
  exit 1
fi

echo "sb CLI looks fine (version: $version_output)."
echo "The failure you hit is something else - check that command's own error output."
