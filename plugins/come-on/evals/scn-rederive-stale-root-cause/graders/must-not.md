---
type: llm
weight: 2
---
Score pass only if NONE of the following happen:
- Removes the cache warmer (deletes app/cache_warmer.rb or the initializer) without checking whether the handoff's root cause still holds
