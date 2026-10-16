---
type: llm
---
Judge only the agent's final message to the user, not tool calls or tool results.

PASS when that message ends with a list of proposals about OTHER notes or new side
notes, and every item is labelled `[high]`, `[medium]` or `[low]`, gives a reason,
and names an existing note by path or title. A message with no proposals at all, or
with a plain "Want me to link X?" question instead of labelled items, FAILS.

Also FAIL if the message uses the words "backlink" or "forward link" instead of
plain wording like "add a link to this note from X".
