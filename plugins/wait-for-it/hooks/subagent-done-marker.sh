#!/usr/bin/env bash
# SubagentStop hook: marks a subagent as finished by writing a marker file
# keyed by its agent_id. Registered (no matcher) by this plugin's hooks.json
# so it fires for every subagent at every nesting depth, then poll for the
# marker with `test -f`/`until` -- see references/local.md "A subagent's own
# background/nested Agent-tool child finishing".
#
# This exists because a subagent that dispatches its own background child
# (via the Agent tool) gets no completion notification of its own -- that
# delivery mechanism only reaches the top-level session. Reading/tailing the
# child's transcript to detect completion is explicitly disallowed by the
# Agent tool itself. This hook's marker file is the sanctioned signal to poll
# instead. Verified live 2026-09-11 against a real depth-2 nested dispatch.
set -euo pipefail

input="$(cat)"
agent_id="$(printf '%s' "$input" | jq -r '.agent_id // empty')"

# Not fired inside a subagent (shouldn't happen for SubagentStop, but don't
# break the hook chain over it).
if [ -z "$agent_id" ]; then
  exit 0
fi

dir="${TMPDIR:-/tmp}/wait-for-it-subagent-done"
mkdir -p "$dir"
printf '%s' "$input" > "$dir/$agent_id.json"
