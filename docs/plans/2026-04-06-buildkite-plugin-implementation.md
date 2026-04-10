# Buildkite Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a `buildkite` Claude Code plugin that consolidates buildkite skills from ci-cd-tools and adds a PreToolUse hook to enforce bktide tool preferences.

**Architecture:** New plugin in the pickled-claude-plugins monorepo. Shell hook reads YAML config, intercepts specific `bk` subcommands via regex, blocks or warns. Skills moved from ci-cd-tools as-is with minor SKILL.md updates.

**Tech Stack:** Bash (hook script), YAML (config), Claude Code plugin system (hooks.json, plugin.json, routes.json)

**Spec:** [2026-04-06-buildkite-plugin-design.md](2026-04-06-buildkite-plugin-design.md)

**Worktree:** `repos/pickled-claude-plugins/worktrees/buildkite-plugin/`

---

### Task 1: Create Plugin Scaffold

**Files:**
- Create: `plugins/buildkite/.claude-plugin/plugin.json`
- Create: `plugins/buildkite/.claude-plugin/routes.json`
- Create: `plugins/buildkite/README.md`

- [ ] **Step 1: Create plugin.json**

```json
{
  "name": "buildkite",
  "description": "Buildkite CI tools: build investigation, pipeline development, and tool preference enforcement",
  "author": {
    "name": "Josh Nichols",
    "email": "josh@technicalpickles.com"
  },
  "repository": "https://github.com/technicalpickles/pickled-claude-plugins",
  "license": "MIT"
}
```

- [ ] **Step 2: Create routes.json**

```json
{
  "routes": [
    "./tool-routes.yaml"
  ]
}
```

- [ ] **Step 3: Create README.md**

Brief README explaining the plugin: what it does, config file location, how to customize preferences.

- [ ] **Step 4: Register in marketplace.json**

Add to `.claude-plugin/marketplace.json` plugins array:

```json
{
  "name": "buildkite",
  "source": "./plugins/buildkite",
  "version": "1.0.0"
}
```

- [ ] **Step 5: Commit**

```bash
git add plugins/buildkite/.claude-plugin/plugin.json plugins/buildkite/.claude-plugin/routes.json plugins/buildkite/README.md .claude-plugin/marketplace.json
git commit -m "feat(buildkite): scaffold new plugin"
```

---

### Task 2: Create Config and Defaults

**Files:**
- Create: `plugins/buildkite/config/defaults.yml`

- [ ] **Step 1: Create defaults.yml**

```yaml
# Buildkite tool preferences
# User config: ~/.config/pickled-claude-plugins/buildkite.yml
# Copy this file there to customize.

tool_preference:
  - bktide
  - mcp
  - bk

strict: true  # true = block non-preferred tools, false = warn

intercept:
  - pattern: "^bk build\\b"
  - pattern: "^bk job log\\b"
  - pattern: "^bk api.*/builds"
```

- [ ] **Step 2: Commit**

```bash
git add plugins/buildkite/config/defaults.yml
git commit -m "feat(buildkite): add default config with tool preferences"
```

---

### Task 3: Write the Hook Script

**Files:**
- Create: `plugins/buildkite/hooks/hooks.json`
- Create: `plugins/buildkite/hooks/check-bk-preference.sh`

- [ ] **Step 1: Create hooks.json**

```json
{
  "description": "Enforce buildkite tool preferences (bktide over bk CLI)",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/check-bk-preference.sh"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 2: Create check-bk-preference.sh**

The script:
1. Reads JSON from stdin, extracts the `command` field from `tool_input`
2. Loads config from `~/.config/pickled-claude-plugins/buildkite.yml`, falling back to `$CLAUDE_PLUGIN_ROOT/config/defaults.yml`
3. Checks command against intercept patterns
4. If match + strict: exit 2 with block message on stderr
5. If match + not strict: print warning on stderr, exit 0
6. If no match: exit 0 silently

```bash
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
```

- [ ] **Step 3: Make script executable**

Run: `chmod +x plugins/buildkite/hooks/check-bk-preference.sh`

- [ ] **Step 4: Test the hook locally**

Create a test input file and pipe it through the script:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"bk build view 1234"}}' | \
  CLAUDE_PLUGIN_ROOT="$PWD/plugins/buildkite" \
  bash plugins/buildkite/hooks/check-bk-preference.sh
```

Expected: exit 2, stderr shows block message mentioning bktide.

Test a non-matching command:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"bk auth status"}}' | \
  CLAUDE_PLUGIN_ROOT="$PWD/plugins/buildkite" \
  bash plugins/buildkite/hooks/check-bk-preference.sh
```

Expected: exit 0, no output.

- [ ] **Step 5: Commit**

```bash
git add plugins/buildkite/hooks/hooks.json plugins/buildkite/hooks/check-bk-preference.sh
git commit -m "feat(buildkite): add PreToolUse hook for bk CLI interception"
```

---

### Task 4: Move Skills from ci-cd-tools

**Files:**
- Move: `plugins/ci-cd-tools/skills/working-with-buildkite-builds/` to `plugins/buildkite/skills/working-with-buildkite-builds/`
- Move: `plugins/ci-cd-tools/skills/developing-buildkite-pipelines/` to `plugins/buildkite/skills/developing-buildkite-pipelines/`

- [ ] **Step 1: Move working-with-buildkite-builds**

```bash
mkdir -p plugins/buildkite/skills
mv plugins/ci-cd-tools/skills/working-with-buildkite-builds plugins/buildkite/skills/
```

- [ ] **Step 2: Move developing-buildkite-pipelines**

```bash
mv plugins/ci-cd-tools/skills/developing-buildkite-pipelines plugins/buildkite/skills/
```

- [ ] **Step 3: Verify ci-cd-tools skills directory**

```bash
ls plugins/ci-cd-tools/skills/
```

Expected: empty (or directory doesn't exist). If empty, remove it:

```bash
rmdir plugins/ci-cd-tools/skills/
```

- [ ] **Step 4: Commit**

```bash
git add plugins/buildkite/skills/ plugins/ci-cd-tools/skills/
git commit -m "feat(buildkite): move buildkite skills from ci-cd-tools"
```

---

### Task 5: Move WebFetch Route

**Files:**
- Move: `plugins/ci-cd-tools/skills/working-with-buildkite-builds/tool-routes.yaml` content to `plugins/buildkite/tool-routes.yaml`
- Modify: `plugins/ci-cd-tools/.claude-plugin/routes.json`

Note: The file was already moved as part of the skills directory in Task 4. It's now at `plugins/buildkite/skills/working-with-buildkite-builds/tool-routes.yaml`. We need to copy it to the plugin root (where routes.json expects it) and remove the old routes.json reference.

- [ ] **Step 1: Copy tool-routes.yaml to plugin root**

```bash
cp plugins/buildkite/skills/working-with-buildkite-builds/tool-routes.yaml plugins/buildkite/tool-routes.yaml
```

- [ ] **Step 2: Remove the old copy from within the skill**

```bash
rm plugins/buildkite/skills/working-with-buildkite-builds/tool-routes.yaml
```

- [ ] **Step 3: Update ci-cd-tools routes.json**

The file currently points to the buildkite route. Since that's gone, either empty it or remove it.

Check current content of `plugins/ci-cd-tools/.claude-plugin/routes.json`. If it only contains the buildkite route reference, replace with:

```json
{
  "routes": []
}
```

- [ ] **Step 4: Commit**

```bash
git add plugins/buildkite/tool-routes.yaml plugins/buildkite/skills/working-with-buildkite-builds/tool-routes.yaml plugins/ci-cd-tools/.claude-plugin/routes.json
git commit -m "feat(buildkite): move WebFetch route from ci-cd-tools"
```

---

### Task 6: Update working-with-buildkite-builds SKILL.md

**Files:**
- Modify: `plugins/buildkite/skills/working-with-buildkite-builds/SKILL.md`

- [ ] **Step 1: Add "Why bktide snapshot?" section**

Add after the `## Overview` section but before `## When to Use This Skill`:

```markdown
## Why bktide snapshot?

One command, one URL, gets you everything: build metadata, annotations, and logs for failed steps, all saved to local files you can grep and re-read without burning API calls. The other tools require you to piece together multiple calls and keep track of job UUIDs vs step IDs.
```

- [ ] **Step 2: Add config override note to Tool Hierarchy section**

After the existing tool hierarchy table/section, add:

```markdown
> This tool preference order can be overridden via `~/.config/pickled-claude-plugins/buildkite.yml`. A PreToolUse hook enforces your preference by intercepting `bk` CLI commands that overlap with bktide capabilities.
```

- [ ] **Step 3: Commit**

```bash
git add plugins/buildkite/skills/working-with-buildkite-builds/SKILL.md
git commit -m "feat(buildkite): add bktide rationale and config override note to skill"
```

---

### Task 7: End-to-End Verification

- [ ] **Step 1: Verify plugin structure**

```bash
find plugins/buildkite -type f | sort
```

Expected output should match the spec's plugin structure.

- [ ] **Step 2: Verify ci-cd-tools still has fix-ci**

```bash
ls plugins/ci-cd-tools/commands/fix-ci.md
```

Expected: file exists.

- [ ] **Step 3: Verify hook script works with all intercept patterns**

```bash
# Should block
echo '{"tool_name":"Bash","tool_input":{"command":"bk build view 1234"}}' | \
  CLAUDE_PLUGIN_ROOT="$PWD/plugins/buildkite" bash plugins/buildkite/hooks/check-bk-preference.sh 2>&1; echo "exit: $?"

echo '{"tool_name":"Bash","tool_input":{"command":"bk job log abc-123"}}' | \
  CLAUDE_PLUGIN_ROOT="$PWD/plugins/buildkite" bash plugins/buildkite/hooks/check-bk-preference.sh 2>&1; echo "exit: $?"

echo '{"tool_name":"Bash","tool_input":{"command":"bk api /v2/organizations/gusto/pipelines/zenpayroll/builds/123"}}' | \
  CLAUDE_PLUGIN_ROOT="$PWD/plugins/buildkite" bash plugins/buildkite/hooks/check-bk-preference.sh 2>&1; echo "exit: $?"

# Should pass through
echo '{"tool_name":"Bash","tool_input":{"command":"bk auth status"}}' | \
  CLAUDE_PLUGIN_ROOT="$PWD/plugins/buildkite" bash plugins/buildkite/hooks/check-bk-preference.sh 2>&1; echo "exit: $?"

echo '{"tool_name":"Bash","tool_input":{"command":"bk config list"}}' | \
  CLAUDE_PLUGIN_ROOT="$PWD/plugins/buildkite" bash plugins/buildkite/hooks/check-bk-preference.sh 2>&1; echo "exit: $?"

echo '{"tool_name":"Bash","tool_input":{"command":"git push"}}' | \
  CLAUDE_PLUGIN_ROOT="$PWD/plugins/buildkite" bash plugins/buildkite/hooks/check-bk-preference.sh 2>&1; echo "exit: $?"
```

- [ ] **Step 4: Test strict=false behavior**

Create a temporary user config with strict=false, run the hook, then clean up:

```bash
mkdir -p ~/.config/pickled-claude-plugins
cat > ~/.config/pickled-claude-plugins/buildkite.yml << 'YAML'
tool_preference:
  - bktide
  - mcp
  - bk
strict: false
intercept:
  - pattern: "^bk build\\b"
  - pattern: "^bk job log\\b"
  - pattern: "^bk api.*/builds"
YAML

echo '{"tool_name":"Bash","tool_input":{"command":"bk build view 1234"}}' | \
  CLAUDE_PLUGIN_ROOT="$PWD/plugins/buildkite" bash plugins/buildkite/hooks/check-bk-preference.sh 2>&1; echo "exit: $?"

rm ~/.config/pickled-claude-plugins/buildkite.yml
```

Expected: exit 0 (not 2), but stderr still shows the warning message.

- [ ] **Step 5: Verify marketplace.json is valid JSON**

```bash
jq . .claude-plugin/marketplace.json
```

Expected: valid JSON with the new buildkite entry.

- [ ] **Step 6: Final commit if any cleanup needed**

```bash
git add -p  # review any remaining changes
git commit -m "chore(buildkite): verification cleanup"
```
