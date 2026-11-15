---
type: regex
target:
  source: file
  path: ".eval/latest-note.md"
flags: mi
match: contains
pattern: "^\\s*[-*] .*incremental"
---
The source's four parallel features are a bulleted list, not a prose paragraph.
