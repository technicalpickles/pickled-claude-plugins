---
type: regex
target:
  source: file
  path: ".eval/latest-note.md"
match: contains
pattern: "https://example\\.com/roc-rs\\b"
---
Keeps the source's outbound link to roc-rs.
