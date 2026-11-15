---
type: regex
target:
  source: file
  path: "vault/fixed.md"
match: contains
pattern: "hello"
---
Fixed-path file target works relative to the run cwd.
