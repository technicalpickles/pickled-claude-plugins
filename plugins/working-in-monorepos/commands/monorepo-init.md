---
name: monorepo-init
description: Initialize monorepo configuration and activate working-in-monorepos skill
---

Run monorepo-init script to detect subprojects and generate .monorepo.json.

Preview detection:
```bash
"${CLAUDE_PLUGIN_ROOT}/skills/working-in-monorepos/scripts/monorepo-init" --dry-run
```

Write configuration:
```bash
"${CLAUDE_PLUGIN_ROOT}/skills/working-in-monorepos/scripts/monorepo-init" --write
```

After writing the configuration, activate the working-in-monorepos skill to enable enhanced monorepo navigation.
