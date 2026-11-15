---
type: llm
weight: 2
---
- Consults the existing retry prior art before recommending (the base_job retry convention and/or the non-idempotent charge job note)
- Surfaces more than one option with their tradeoffs rather than only one pick
- Each option includes what you get, the tradeoff, and the evidence (file or line) behind it
- Gives a clear recommendation with reasoning
- Hands the decision back to the user (or asks) before implementing, rather than just implementing its own choice
