---
runs: 3
max_turns: 3
allowed_tools: [Read, Glob, Grep, Skill]
tags: [trigger, tune]
---

watch acme/web PR #3100's checks until they all settle. i just pushed an empty commit to retrigger CI
