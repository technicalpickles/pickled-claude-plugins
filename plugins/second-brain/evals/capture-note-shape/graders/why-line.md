---
type: regex
target:
  source: file
  path: ".eval/latest-note.md"
flags: i
match: contains
pattern: "\\*\\*Why I saved this:\\*\\*[^\\n]*roguelike"
---
Records why it was saved, from the reason in the request.
