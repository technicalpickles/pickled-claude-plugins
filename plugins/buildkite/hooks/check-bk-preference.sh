#!/usr/bin/env bash
set -euo pipefail

# Read hook input from stdin
INPUT=$(cat)

# Extract the command from tool_input
# tool_input for Bash has a "command" field
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# No command? Not our problem.
if [ -z "$COMMAND" ]; then
  exit 0
fi

# Load config: user config first, then plugin defaults
USER_CONFIG="$HOME/.config/pickled-claude-plugins/buildkite.yml"
PLUGIN_CONFIG="${CLAUDE_PLUGIN_ROOT}/config/defaults.yml"

if [ -f "$USER_CONFIG" ]; then
  CONFIG_FILE="$USER_CONFIG"
elif [ -f "$PLUGIN_CONFIG" ]; then
  CONFIG_FILE="$PLUGIN_CONFIG"
else
  # No config at all, pass through
  exit 0
fi

# Parse config using python for portable YAML parsing
# Each value extracted separately to avoid shell word-splitting bugs
STRICT=$(python3 -c "
import yaml
with open('$CONFIG_FILE') as f:
    c = yaml.safe_load(f)
print('true' if c.get('strict', True) else 'false')
")

TOOL_PREF=$(python3 -c "
import yaml
with open('$CONFIG_FILE') as f:
    c = yaml.safe_load(f)
print(' > '.join(c.get('tool_preference', ['bktide', 'mcp', 'bk'])))
")

PREFERRED=$(python3 -c "
import yaml
with open('$CONFIG_FILE') as f:
    c = yaml.safe_load(f)
print(c.get('tool_preference', ['bktide'])[0])
")

# Check each intercept pattern against the command
MATCHED=$(python3 -c "
import yaml, re
with open('$CONFIG_FILE') as f:
    c = yaml.safe_load(f)
command = '''$COMMAND'''
for entry in c.get('intercept', []):
    if re.search(entry['pattern'], command):
        print('true')
        break
else:
    print('false')
")

if [ "$MATCHED" = "false" ]; then
  exit 0
fi

# Compose the message
MSG="Your buildkite tool preference is: ${TOOL_PREF}

The command \`${COMMAND}\` was intercepted. Your preferred tool is ${PREFERRED}.
Use \`npx bktide@latest snapshot <buildkite-url>\` for build investigation,
or \`npx bktide@latest --help\` for other commands.

To allow bk commands, set \`strict: false\` in ~/.config/pickled-claude-plugins/buildkite.yml"

if [ "$STRICT" = "true" ]; then
  echo "$MSG" >&2
  exit 2
else
  echo "$MSG" >&2
  exit 0
fi
