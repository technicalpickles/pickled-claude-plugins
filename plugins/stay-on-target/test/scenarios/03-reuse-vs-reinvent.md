---
name: reuse-vs-reinvent
description: User wants to add functionality that partially exists
git_ref: main
cwd: ~/workspace/bktide
criteria:
  - prior_art
  - clarification
  - exploration
---

# User Message

let's switch to GraphQL

# Expected Behaviors

- Should explore codebase for existing GraphQL infrastructure
- Should find @apollo/client in package.json
- Should find any existing schema definitions
- Should present findings before proposing new work
- Should offer options: build on existing, explore why it's structured this way, or different approach

# Context

Fresh session start - no prior conversation.
The bktide project has partial Apollo client setup but no server-side GraphQL.
