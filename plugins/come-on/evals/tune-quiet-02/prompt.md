---
runs: 3
max_turns: 3
allowed_tools: [Read, Glob, Grep, Skill]
---

tl;dr this for me, it's the README I wrote last night:

# rates
Fetches FX rates hourly from the ECB feed and caches them in redis for 2h. Run `bin/rates sync` to force a refresh.
