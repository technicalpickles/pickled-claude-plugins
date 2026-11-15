---
type: regex
target:
  source: file
  path: ".eval/latest-note.md"
flags: m
match: contains
pattern: "^created: \\d{4}-\\d{2}-\\d{2}$"
---
Frontmatter has a created date.
