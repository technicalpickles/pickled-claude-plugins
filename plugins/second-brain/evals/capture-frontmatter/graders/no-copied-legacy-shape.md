---
type: regex
target:
  source: file
  path: ".eval/latest-note.md"
flags: m
match: not_contains
pattern: "^(status: filed|type: reference|tags: \\[#)"
---
Did not copy the routed neighbor note's legacy frontmatter shape.
