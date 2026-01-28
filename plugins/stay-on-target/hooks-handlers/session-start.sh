#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPTS_DIR="$SCRIPT_DIR/../prompts"

# Compose prompt from modular files
# Order matters: base first, then behaviors in numbered order
PROMPT_CONTENT=""

# Base philosophy
if [[ -f "$PROMPTS_DIR/_base.md" ]]; then
    PROMPT_CONTENT+=$(cat "$PROMPTS_DIR/_base.md")
    PROMPT_CONTENT+=$'\n\n'
fi

# Behaviors (sorted by number prefix)
for behavior_file in "$PROMPTS_DIR/behaviors/"*.md; do
    if [[ -f "$behavior_file" ]]; then
        PROMPT_CONTENT+=$(cat "$behavior_file")
        PROMPT_CONTENT+=$'\n\n'
    fi
done

# Escape for JSON
ESCAPED_CONTENT=$(printf '%s' "$PROMPT_CONTENT" | jq -Rs .)

cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": $ESCAPED_CONTENT
  }
}
EOF

exit 0
