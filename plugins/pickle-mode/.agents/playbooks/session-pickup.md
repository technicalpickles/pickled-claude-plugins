---
extends: session-pickup
when: Resuming prior work in a session that has the agent-meta plugin.
---

# Session pickup, through agent-meta:unpark

- **Replace** "Read the project checkpoint first" Invoke `agent-meta:unpark` through the Skill tool to find and read the handoff. Call the Skill tool rather than reading the file, because hooks key off that invocation. Skip unpark's "Proceed?" prompt. When its validation passes, continue. When it reports staleness, record the issues and continue to step 2, which rebuilds state from the repository anyway. When no handoff exists, search prior sessions with the `cq` skill when it is installed, and otherwise use the transcript fallback in the bundled step.
