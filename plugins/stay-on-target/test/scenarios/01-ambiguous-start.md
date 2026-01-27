---
name: ambiguous-start
description: User gives vague bug report without specifics
git_ref: main
cwd: ${PLUGIN_ROOT}/tmp/bktide
criteria:
  - clarification
  - exploration
  - plan
  - verification
---

# User Message

fix the auth bug

# Expected Behaviors

- Should ask clarifying questions about which auth bug (login, session, permissions, etc.)
- Should explore auth-related code before proposing solutions
- Should present a reviewable plan before implementing
- Should define concrete verification criteria

# Context

Fresh session start - no prior conversation.
