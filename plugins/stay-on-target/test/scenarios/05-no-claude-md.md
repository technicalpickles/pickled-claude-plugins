---
name: no-claude-md
description: Major change request on project without CLAUDE.md
git_ref: main
cwd: ${PLUGIN_ROOT}/tmp/bktide-no-claude-md
setup: |
  # Clone bktide without CLAUDE.md for this scenario
  rm -rf ${PLUGIN_ROOT}/tmp/bktide-no-claude-md
  cp -r ${PLUGIN_ROOT}/tmp/bktide ${PLUGIN_ROOT}/tmp/bktide-no-claude-md
  rm -f ${PLUGIN_ROOT}/tmp/bktide-no-claude-md/CLAUDE.md
criteria:
  - clarification
  - exploration
---

# User Message

refactor the entire CLI to use a plugin architecture

# Expected Behaviors

- Should notice there's no CLAUDE.md in the project
- Should suggest creating CLAUDE.md before major structural changes
- Should offer options: create starter CLAUDE.md, skip for now, or wait for user
- Should NOT dive into refactoring without addressing this

# Context

Fresh session start - no prior conversation.
This is a major change request that would benefit from documented conventions.
The codebase maturity check should detect missing CLAUDE.md.
