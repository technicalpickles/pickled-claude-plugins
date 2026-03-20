---
description: Research a topic, look something up, or explore a subject using a sandboxed web research agent
argument-hint: [topic to research]
allowed-tools:
  - Bash(${CLAUDE_PLUGIN_ROOT}/scripts/research.sh:*)
  - Read(./research/**)
  - Glob(./research/**)
---

# Research

Run a sandboxed web research agent that searches the web, fetches pages, and produces a markdown report.

Load the `research-agent:research` skill and follow its instructions.

**If argument provided:** Use the argument as the research topic and proceed directly to research execution (skip clarification).

**If no argument:** Follow the guided flow in the skill to clarify the research topic, scope, and any specific angles.
