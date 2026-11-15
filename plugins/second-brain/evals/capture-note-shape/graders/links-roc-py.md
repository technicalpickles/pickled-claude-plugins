---
type: regex
target:
  source: file
  path: ".eval/latest-note.md"
match: contains
pattern: "https://example\\.com/roc-py\\b"
---
Keeps the source's outbound link to roc-py.
