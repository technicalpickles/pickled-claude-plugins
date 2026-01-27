---
name: feature-creep
description: User requests additional feature while doing a bug fix
git_ref: main
cwd: ${PLUGIN_ROOT}/tmp/bktide
conversation:
  - role: assistant
    content: |
      I'll help you fix the build status display bug.

      Looking at the status display code...
      Found: src/commands/builds/show.ts has the status rendering

      The issue is that failed steps aren't being highlighted properly.

      Plan:
      - Fix status highlighting in src/commands/builds/show.ts
      - Add test for failed step display

      Ready to proceed?
      (A) Looks good, go ahead
      (B) Let me adjust the plan
      (C) I have questions first
  - role: user
    content: "A"
  - role: assistant
    content: |
      Implementing the fix...

      Fixed the status highlighting. Failed steps now show in red.
      Tests pass.
criteria:
  - drift_detection
---

# User Message

nice! while we're in here, can you also add notifications when builds fail?

# Expected Behaviors

- Should recognize "while we're here" as feature creep signal
- Should flag this as scope drift (new feature vs bug fix)
- Should pause and offer A/B/C options:
  - (A) Explore here - add notifications in this thread
  - (B) Branch now - start focused conversation on notifications
  - (C) Note for later - finish bug fix first, save notification context
- Should NOT just start implementing notifications

# Context

Mid-conversation - user approved a bug fix plan but now requesting new feature.
"While we're here" is a classic feature creep phrase.
Bug fixes should stay focused - new features are separate scope.
