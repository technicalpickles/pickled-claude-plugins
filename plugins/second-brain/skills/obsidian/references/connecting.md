# Connection Discovery Reference

Systematic algorithm for finding related notes in the vault and weaving connections between them.

**Key principle:** Connections are bidirectional. When you link a new note to an existing one, also offer to update the existing note to link back. Notes with `TK` placeholders or `## See Also` sections are explicitly waiting for connections.

## Prerequisites

Before running connection discovery:

```bash
# Verify qmd is available
which qmd
```

If not found, inform user and skip connections (don't fail the capture workflow):
```
qmd not installed - skipping connection discovery.
Install via: bun add -g qmd
```

Load collection name from `~/.claude/second-brain.md` (`qmd_collection` setting under the vault's settings section). If not set, default to `second-brain`.

Verify the collection exists:
```bash
qmd collection list
```

---

## Step 1: Extract Query Terms

From the note being connected, build a natural language query string:

1. **Title keywords** - Strip the Zettelkasten timestamp prefix, use the remaining words
2. **Key phrases from body** - Extract the most distinctive 2-3 phrases (not generic words like "the" or "about")
3. **Tags** - Include any frontmatter tags or inline tags

Build a single query string. Keep it natural, not a keyword dump. qmd handles expansion and semantic matching.

**Example:**
- Note title: `202603041430 karafka consumer group rebalancing strategy`
- Body mentions: "multi-tenant consumers", "cooperative sticky assignor", "session timeout"
- Query: `karafka consumer group rebalancing multi-tenant cooperative sticky assignor`

---

## Step 2: Run Semantic Search

```bash
qmd query "{query}" -c {collection} -n 15 --json
```

Request 15 results to allow for filtering. The JSON output contains:
- `file`: `qmd://{collection}/{path}` (strip the prefix to get vault-relative path)
- `score`: 0.0-1.0 relevance score
- `title`: document title
- `snippet`: matching content with context markers

---

## Step 3: Filter Noise

Remove results that shouldn't be connection candidates:

### 3a: Remove Self

If the note being connected appears in results, remove it. Match by filename (the Zettelkasten timestamp prefix is unique enough).

### 3b: Remove Already-Linked Notes

Parse the note's content for existing `[[wiki-links]]`. Any note already referenced is not a new connection candidate.

```
Pattern: \[\[([^\]]+)\]\]
```

Extract link targets, match against result filenames (without extension).

### 3c: Remove Low-Relevance Results

Drop any result with score below 0.30 (30%). This is a starting threshold, may need tuning.

### 3d: Remove Daily Notes

Filter out results that are daily notes (`Fleeting/YYYY-MM-DD.md` pattern). These are temporal, not topical connections. They add noise without value.

---

## Step 4: Enrich Candidates

For each remaining candidate, gather connection signals:

### 4a: Check for Connection-Ready Sections

Read the candidate note (use `qmd get` for efficiency) and check for:

- **`## See Also`** section exists
- **`## Related`** section exists
- **`TK`** appears in the note body (placeholder explicitly waiting for content)

### 4b: Check PARA Location

Extract the candidate's PARA category from its path:
- `*Projects*/` = active project context
- `*Areas*/` = ongoing area of responsibility
- `*Resources*/` = reference material
- `Fleeting/` or `Inbox/` = not yet organized

Compare to the note being connected. Same PARA area = topically adjacent.

### 4c: Check Modification Recency

From qmd metadata or file stat, note when the candidate was last modified. Recent = more likely to be actively relevant.

---

## Step 5: Rank by Connection Value

Score each candidate using the qmd relevance as baseline, then apply boosts:

| Signal | Effect | Reasoning |
|--------|--------|-----------|
| qmd relevance score | Primary (0-100%) | Semantic similarity is the strongest signal |
| Has `TK` placeholder | +15% boost | Note is explicitly waiting for connections |
| Same PARA area | +5% boost | Topically adjacent, likely related |
| Modified in last 30 days | +5% boost | Fresh content, more actively relevant |

Cap final score at 99%.

Sort candidates by final score, descending.

---

## Step 6: Present Candidates

Show the top candidates (max 7, enough for a meaningful selection without overwhelming):

```
Found {N} related notes:

1. **{title}** ({score}%)
   `{path relative to vault}`
   > "{snippet, 1-2 lines}"
   {signals: "(has TK placeholder)", "(same area)", etc.}

2. **{title}** ({score}%)
   ...
```

Use AskUserQuestion with multi-select to let the user choose which to connect:

**Question:** "Which notes should I connect to {note title}?"

Include option: "Skip connections" (always available)

If no candidates above threshold after filtering, skip silently or note:
```
No strong connections found for this note.
```

---

## Step 7: Add Forward Links

For each selected connection, add a wiki-link in the note being connected.

### If `## Related` Section Exists

Append to it:

```markdown
## Related

- [[existing-link]] - existing description
- [[{new-connection-filename}]] - {brief description of relationship}
```

### If No `## Related` Section

Add one before the trailing `---` and capture signature (if present), or at the end of the note:

```markdown
## Related

- [[{new-connection-filename}]] - {brief description of relationship}
```

### Link Description Guidelines

The description should capture WHY these notes are related, not just repeat the title:

| Good | Bad |
|------|-----|
| "Consumer group architecture patterns" | "Kafka consumer groups" |
| "Same rebalancing issue in production" | "Related note" |
| "Guild discussion on DLQs and consumer groups" | "Meeting notes" |

---

## Step 8: Offer Backlink Weaving

After forward links are added, check if any selected notes have connection-ready sections:

- Has `## See Also` section
- Has `## Related` section
- Has `TK` placeholder in body

If any do, offer backlink weaving:

```
{N} of your selected notes have See Also/Related sections or TK placeholders.
Want me to add backlinks from them to your new note?

(A) Yes, add backlinks to all that have See Also/Related/TK
(B) Let me pick which ones
(C) Skip backlinks, just keep forward links
```

### Adding Backlinks

For each note where backlinks are accepted:

**If `## See Also` exists:** Append wiki-link to that section
**If `## Related` exists:** Append wiki-link to that section
**If both exist:** Use `## See Also` (prefer the existing convention)
**If neither exists but has `TK`:** Do not add a section, only replace TK if the TK is clearly a placeholder for this connection

### Replacing TK Placeholders

`TK` is "to come" - a deliberate placeholder. Only replace if the TK appears in a context where the new note is a clear fit:

```markdown
# Before
See also TK for rebalancing strategies.

# After
See also [[202603041430 rebalancing-strategy]] for rebalancing strategies.
```

If the TK context doesn't match the new note, leave it alone.

### Backlink Description

Same format as forward links. Describe the relationship from the existing note's perspective:

```markdown
- [[202603041430 rebalancing-strategy]] - Rebalancing approach for multi-tenant consumers
```

---

## Step 9: Confirm Results

After all connections are made, summarize:

```
Connections added:

Forward links (in {note title}):
- [[note-a]] - description
- [[note-b]] - description

Backlinks added:
- note-a: added to ## See Also
- note-b: replaced TK placeholder

{N} notes are now connected.
```

---

## Implementation Pattern

When integrating into a command:

```markdown
## After Routing: Discover Connections

Follow `references/connecting.md` algorithm:

1. Check qmd prerequisites (skip if not available)
2. Extract query terms from note content
3. Run semantic search via qmd
4. Filter noise (self, already-linked, low-relevance, daily notes)
5. Enrich and rank candidates
6. Present candidates for user selection (multi-select)
7. Add forward links (## Related section)
8. Offer backlink weaving for selected notes
9. Confirm what was connected

This step is best-effort: don't fail capture if connection discovery fails.
```

---

## Batch Connection Discovery

When connecting multiple notes at once (e.g., `/distill-conversation`):

1. Run discovery for each note independently
2. Collect all suggestions
3. Present as batch summary:

```
Found connections for {M} of {N} captured notes:

- {Note A title}: {count} related notes
- {Note C title}: {count} related notes

(A) Review and connect all
(B) Skip connections for now
```

If user picks (A), walk through each note's connections using the standard presentation and selection flow.

**Deduplication:** If the same candidate appears for multiple captured notes, that's fine. Each connection is independent and the relationship description will differ.

---

## Constraints

- **Best-effort** - Don't fail capture or routing if connection discovery fails
- **User selects** - Never auto-connect, always present candidates for selection
- **Wiki-link format** - Use `[[filename]]` not `[text](path)`, no `.md` extension in links
- **Descriptive links** - Always include a brief description of the relationship
- **Respect existing structure** - Append to existing sections, don't reorganize notes
- **Skip daily notes** - Daily notes are temporal, not topical connections
- **Index freshness** - New captures won't be in qmd index yet, that's expected (we query FROM the new note's content, not for it)
