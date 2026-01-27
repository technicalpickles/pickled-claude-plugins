---
name: false-positive
description: Natural extension of task that should NOT trigger drift detection
git_ref: main
cwd: ${PLUGIN_ROOT}/tmp/bktide
conversation:
  - role: assistant
    content: |
      I'll help you fix the pagination bug in the builds list.

      Looking at the builds list code...
      Found: src/commands/builds/list.ts handles the pagination

      The issue is that offset isn't being passed correctly to the API.

      Plan:
      - Fix offset calculation in src/commands/builds/list.ts
      - Add test for pagination edge cases

      Ready to proceed?
      (A) Looks good, go ahead
      (B) Let me adjust the plan
      (C) I have questions first
  - role: user
    content: "A"
  - role: assistant
    content: |
      Implementing the fix...

      Fixed the offset calculation. Now running tests...
      Tests pass.
criteria:
  - escape_hatch
---

# User Message

can you also add a --page flag so users can jump to a specific page?

# Expected Behaviors

- Should recognize this as a natural extension of the pagination work
- Should NOT flag this as scope drift
- Should proceed with adding the feature as part of current work
- May briefly acknowledge it's related to current work

# Context

Mid-conversation - user has already approved a plan to fix pagination.
Adding a page flag is a natural extension of pagination work, not scope drift.
This tests false positive avoidance in drift detection.
