---
type: regex
target:
  source: file
  path: ".eval/latest-note.md"
flags: m
match: contains
pattern: "^status: seedling$"
---
Fresh capture carries the zettelkasten maturity status.
