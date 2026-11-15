#!/usr/bin/env bash
# SessionStart nudge: devlog's description-based triggering measured ~0
# real invocations after launch (checked via cq over session transcripts).
# A standing instruction planted at session start only fires once, but it
# governs the whole session.

# devlog_mode (userConfig) = sidechain hands entry-writing to the devlog-sidechain
# mod, so stay silent. Unset (older Claude Code, or never configured) means nudge.
if [ "${CLAUDE_PLUGIN_OPTION_DEVLOG_MODE:-nudge}" = "sidechain" ]; then
  exit 0
fi

read -r -d '' CONTEXT <<'EOF'
## Devlog

This session has the `second-brain:devlog` skill available. Use it the
moment one of these happens - don't ask, don't offer, just write it in the
same turn:

- You finish a feature or fix a notable bug
- You wrap up a work session
- You discover something non-obvious: a gotcha, undocumented behavior, a
  workaround that took several tries, a constraint you only noticed after
  hitting it

Don't use it for routing/connecting/moving notes (`process-inbox`'s job) or
for writing up an external source (`second-brain:capture`'s job).
EOF

ESCAPED_CONTEXT=$(printf '%s' "$CONTEXT" | jq -Rs .)

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": $ESCAPED_CONTEXT
  }
}
EOF

exit 0
