---
type: regex
target:
  source: file
  path: ".eval/latest-note.md"
flags: m
match: not_contains
pattern: "^(source: manual|repo: none|branch: none|commit: none)$"
---
sb's provenance placeholders were dropped.
