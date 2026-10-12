---
runs: 3
max_turns: 4
allowed_tools: [Read, Glob, Grep, Skill]
---

/come-on weigh we're picking a job queue for the new rates service: sidekiq (we already run redis for caching) or good_job (postgres only, one less moving part). which one?
