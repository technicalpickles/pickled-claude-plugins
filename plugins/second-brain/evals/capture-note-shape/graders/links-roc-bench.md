---
type: regex
target:
  source: file
  path: ".eval/latest-note.md"
match: contains
pattern: "https://example\\.com/roc-bench\\b"
---
Keeps the source's outbound link to roc-bench.
