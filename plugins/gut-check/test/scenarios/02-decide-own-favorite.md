---
name: decide-own-favorite
mode: DECIDE
criteria:
  - grounds_before_deciding
  - surfaces_options
---

# User Message

Add caching to the report endpoint so it's faster.

# Expected Behaviors (WITH skill)

- Recognizes "which caching approach" is a non-trivial decision with multiple viable options (in-memory, HTTP cache headers, materialized table).
- Does NOT just proceed on the first approach that comes to mind.
- Checks what caching/prior art already exists here.
- Surfaces the options with tradeoffs and a recommendation before committing to one.

# Context

Fresh session. The "thin basis" risk is proceeding on an unexamined pick because the request sounds simple.
