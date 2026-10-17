---
type: llm
focus:
  source: file
  path: ".eval/latest-note.md"
---
The note's claims about Roc come only from this source text:

"Roc trades a small amount of preprocessing time for large runtime speedups on
repeated pathfinding queries over the same map, using a hierarchical
decomposition of the search space. It was published in 2026 by Ada Example.
Features: hierarchical map decomposition; incremental updates when the map
changes; bounded-suboptimal paths with a tunable epsilon; parallel query
batching. Implementations: a Rust crate, a Python port, and published
benchmarks."

Judge new information, not wording. PASS when every statement about Roc is the
source's content, including paraphrases, light restatements, and obvious
restatements of the same fact (e.g. "incremental updates" described as
"handles map changes without starting over"). The user's own reason for saving
it, links, headings, and frontmatter are not claims.

FAIL only when the note adds information the source doesn't contain: numbers,
comparisons to other algorithms, specific use cases or examples (e.g. game
scenarios), history, or mechanisms the text doesn't describe.
