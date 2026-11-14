#!/usr/bin/env bash
# Stop: hand off to `hk agent stop-hook`, which is what `hk agent hooks --target
# claude-code` prints. hk does the rest: it runs `hk run check --safe`, stands down
# on stop_hook_active, passes when there is no `check` hook, and always exits 0,
# printing {"decision":"block",...} when the check fails (per hk's docs for
# `agent stop-hook`). This script relays hk's output and exit status unchanged; it
# only decides whether hk is there to ask. 570 and the hook's 600 in hooks.json are
# the seconds `hk agent hooks` prints: hk stops the check at 570 and reports a block,
# which leaves Claude Code's own 600s hook timeout a 30s margin.

# shellcheck source=hk-common.sh
. "$(dirname "${BASH_SOURCE[0]}")/hk-common.sh"

payload=$(cat)
dir=$(hk_payload_dir "$payload")

hk_ready "$dir" || exit 0

cd "$dir" || exit 0
printf '%s' "$payload" | exec hk agent stop-hook --target claude-code --timeout 570
