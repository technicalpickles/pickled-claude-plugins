---
name: scope-drift
description: User explores alternative approach mid-conversation (REST to GraphQL)
git_ref: main
cwd: ${PLUGIN_ROOT}/tmp/bktide
conversation:
  - role: assistant
    content: |
      I'll help you add a new endpoint to fetch build artifacts.

      Looking at the existing REST API structure...
      Found: src/api/routes/builds.ts handles build-related endpoints

      Plan:
      - Add GET /builds/:id/artifacts endpoint in src/api/routes/builds.ts
      - Create artifact fetching logic in src/services/artifacts.ts
      - Add tests for the new endpoint

      Ready to proceed?
      (A) Looks good, go ahead
      (B) Let me adjust the plan
      (C) I have questions first
  - role: user
    content: "A"
  - role: assistant
    content: |
      Implementing the artifacts endpoint...

      Created src/services/artifacts.ts with fetchArtifacts function.
      Now adding the route...
criteria:
  - drift_detection
---

# User Message

actually, what if we used GraphQL instead of REST for this? would that be better?

# Expected Behaviors

- Should recognize this as exploring an alternative to the agreed-upon REST approach
- Should flag this as scope drift (different architecture choice)
- Should pause and offer A/B/C options:
  - (A) Explore here - keep in this thread
  - (B) Branch now - start a focused conversation on GraphQL
  - (C) Note for later - save context and stay on REST task
- Should NOT just start implementing GraphQL

# Context

Mid-conversation - user had approved a REST plan but now asking about GraphQL.
This is the canonical scope drift scenario from the design doc.
