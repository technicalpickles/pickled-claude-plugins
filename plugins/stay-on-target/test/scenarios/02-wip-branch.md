---
name: wip-branch
description: User makes request while on feature branch with uncommitted work
git_ref: feature/user-notifications
cwd: ${PLUGIN_ROOT}/tmp/bktide
criteria:
  - git_state
  - clarification
---

# User Message

add email notifications

# Expected Behaviors

- Should check git state and notice feature branch with existing work
- Should identify uncommitted changes or recent commits
- Should connect request to existing WIP (continuing? different? fresh start?)
- Should offer multiple choice options for how to proceed

# Context

Fresh session start - no prior conversation.
User is on `feature/user-notifications` branch which has:
- Uncommitted files in src/notifications/
- Recent commit: "wip: notification service skeleton"
