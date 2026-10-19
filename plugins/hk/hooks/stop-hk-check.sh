#!/usr/bin/env bash
# Stop: hand off to `hk agent stop-hook`, which is what `hk agent hooks --target
# claude-code` prints. hk does the rest: it runs `hk run check --safe`, stands down
# on stop_hook_active, passes when there is no `check` hook, and always exits 0,
# printing {"decision":"block",...} when the check fails. This script only decides
# whether hk is there to ask.

# shellcheck source=hk-common.sh
. "$(dirname "${BASH_SOURCE[0]}")/hk-common.sh"

payload=$(cat)
dir=$(hk_payload_dir "$payload")

hk_ready "$dir" || exit 0

cd "$dir" || exit 0
printf '%s' "$payload" | exec hk agent stop-hook --target claude-code --timeout 570
