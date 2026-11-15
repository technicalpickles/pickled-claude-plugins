---
type: regex
target:
  source: file
  path: ".eval/latest-note.md"
flags: m
match: contains
pattern: "^source: \\S*roc-article"
---
sb's `source: manual` placeholder was replaced with the actual source.
