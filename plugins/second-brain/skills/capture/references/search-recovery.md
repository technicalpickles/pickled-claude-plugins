# When a search misses or the user rejects the hit

## Search comes up empty

A miss is not proof the note is absent. In order:

1. **Basename is the stable identity.** Notes get routed between folders constantly. Search the
   basename across the whole vault (`Glob`/`Grep`) before concluding anything is missing.
2. **Check both inboxes.** `10-19 System & Capture/11 Inbox & triage/` and
   `10-19 System & Capture/11 Inbox/` are separate folders with the same JD code. `sb inbox list`
   only reads the first.
3. **The note may genuinely not exist.** Say that plainly and offer to start one.

## The user says "that isn't the one"

Do **not** re-run the same query with different phrasing, and do not widen `-n` and hope. Ask for
one distinguishing detail (who made it, where they saw it, what it sits next to) and search on
*that* instead. Re-running near-identical searches has burned entire sessions.
