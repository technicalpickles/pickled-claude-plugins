---
type: regex
target: trace
match: not_contains
pattern: "sb note create[^}]*--dry-run"
---
Creates in one sb call, no wasted --dry-run.
