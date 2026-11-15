---
type: regex
target: trace
match: not_contains
pattern: "\"command\":\\s*\"[^}]*(note create|daily append)|\"name\":\\s*\"(Write|Edit)\""
---
Nothing was written: no note created, no breadcrumb, no Write or Edit.
