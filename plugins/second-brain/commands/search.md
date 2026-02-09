---
description: Search your second brain using semantic search
argument-hint: <query>
allowed-tools:
  - Read(~/.claude/second-brain.md)
  - Read(~/.claude/vaults/**/*.md)
  - Bash(which:qmd)
  - Bash(qmd:query *)
  - Bash(qmd:collection list)
  - Bash(qmd:get *)
---

# Search Second Brain

Search your Obsidian vault using qmd's semantic search (combines BM25 + vector similarity + reranking).

## Prerequisites

- `qmd` must be installed and available in PATH
- A qmd collection must be configured for your vault

## Step 1: Check Prerequisites

Verify qmd is available:
```bash
which qmd
```

If not found, inform user:
```
qmd is not installed. Install it via:
  bun add -g qmd
Then configure a collection:
  qmd collection add ~/path/to/vault --name second-brain
```

## Step 2: Load Configuration

Read `~/.claude/second-brain.md` for vault configuration.

Extract collection name from the `qmd_collection` setting under the vault's settings section.
If not set, default to `second-brain`.

Verify the collection exists:
```bash
qmd collection list
```

If collection doesn't exist, inform user which collections are available and suggest adding one.

## Step 3: Execute Search

**If no argument provided:**
Ask: "What would you like to search for?"

Run the search:
```bash
qmd query "{query}" -c {collection} -n 10 --json
```

## Step 4: Present Results

Parse JSON output. Each result has:
- `file`: `qmd://{collection}/{path}` - strip the `qmd://{collection}/` prefix
- `score`: 0.0-1.0 - convert to percentage
- `title`: document title from frontmatter or first heading
- `snippet`: matching content with diff-like context markers (strip `@@ ... @@` lines)

Present results clearly:

```
## Search Results for "{query}"

1. **{title}** (93%)
   `{path relative to vault}`
   > {cleaned snippet preview, 2-3 lines max}

2. **{title}** (51%)
   ...
```

Include:
- Title from the result
- Relevance score as percentage (score × 100)
- File path relative to vault (strip `qmd://collection/` prefix)
- Snippet preview (clean up diff markers, show meaningful content)

If no results, suggest:
- Try different keywords
- Check if vault has been indexed (`qmd update && qmd embed`)

## Step 5: Offer Follow-up Actions

After showing results, offer to:
- **Read a result** - Use `qmd get "qmd://{collection}/{path}"` to retrieve full content
- **Search again** - Try different or refined terms

If user wants to read a result:
```bash
qmd get "qmd://{collection}/{path}" -l 100
```

This returns the document content with optional line limit.

## Constraints

- **Query required** - Don't search without a query
- **Collection must exist** - Check before searching
- **Show scores** - Help user understand relevance
- **Respect limits** - Default to 10 results, don't overwhelm
