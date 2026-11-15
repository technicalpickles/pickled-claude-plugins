---
type: regex
pattern: 'ci\.log|cache\.rb'
match: contains
target: trace
---
Looks at current evidence (the CI log or the cache config, by any tool) before acting.
