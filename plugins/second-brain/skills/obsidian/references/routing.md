# Note Routing Reference

Systematic algorithm for discovering vault structure and matching notes to destinations.

## Step 1: Discover Vault Structure

**Never guess at paths.** Only suggest destinations that actually exist.

```bash
# List actual PARA folders (handle emoji prefixes)
ls -d "{vault}"/*Projects*/*/  2>/dev/null
ls -d "{vault}"/*Areas*/*/     2>/dev/null
ls -d "{vault}"/*Resources*/*/ 2>/dev/null
```

Build a destination map from the output:

```
Available Destinations:
- Areas/AI/agentic development/
- Areas/gusto/
- Areas/health/
- Resources/software engineering/
- Resources/tools/
- Projects/home-renovation/
```

**Important:**
- Use exact folder names from `ls` output (including emoji prefixes)
- Only go two levels deep (Category/Subcategory/)
- Include Inbox as always-available option

---

## Step 2: Extract Note Signals

From the note being routed, extract:

### Keywords
- Words from title (after timestamp prefix)
- Key terms from body content
- Tags if present

### Content Category
- Architecture decision
- Debugging pattern
- Tool configuration
- Process improvement
- Domain knowledge
- Meeting notes
- Personal insight

### Source Context
From frontmatter provenance:
- `repo:` → maps to work projects
- `branch:` → topic hints
- Conversation topic if captured via `/insight`

---

## Step 3: Match Destinations

Score each discovered destination against the note:

| Signal | Weight | Description |
|--------|--------|-------------|
| Keyword in folder name | 40% | Direct match: "claude" in title → "AI/agentic development/" |
| Related notes in folder | 30% | Grep for similar terms in destination folder |
| PARA category fit | 20% | Is this ongoing (Area), reference (Resource), or active (Project)? |
| Recency | 10% | Recently modified files in folder suggest active use |

### Matching Examples

**Note:** `202601251430 redis-session-caching.md`
- Keywords: "redis", "session", "caching"
- Category: Architecture decision

**Scoring:**
- `Resources/caching/` → 60% (keyword match)
- `Areas/gusto/` → 45% (repo context from work)
- `Resources/software engineering/` → 35% (generic fit)

---

## Step 4: Confidence Levels

| Level | Score | Interpretation |
|-------|-------|----------------|
| **High** | 80-100% | Strong keyword match + related notes exist |
| **Medium** | 50-79% | Partial match or category-only fit |
| **Low** | 20-49% | Weak signals, might fit |
| **None** | <20% | No meaningful match - leave in inbox |

### When to Recommend Inbox

- No destination scores above 20%
- Multiple destinations score equally (unclear fit)
- Note is too generic to categorize
- User should decide after more context emerges

---

## Step 5: Present with Explanations

Always show reasoning so users understand and can correct:

```
Routing suggestions for "202601251430 redis-session-caching.md":

1. **Areas/AI/agentic development/** (88% - High)
   → Matches keywords: "claude", "code"
   → Related note exists: "Claude Code.md"

2. **Resources/software engineering/** (52% - Medium)
   → Generic architecture reference fit
   → No specific keyword match

3. **Leave in Inbox** (Safe default)
   → Route later when clearer destination emerges
```

### Presentation Rules

- Show top 2-3 destinations (not all)
- Include confidence level and percentage
- Explain WHY each destination matched
- Always include "Leave in Inbox" option
- Put recommended option first with "(Recommended)" suffix

---

## Implementation Pattern

When implementing routing in a command:

```markdown
## Routing Analysis

1. Discover destinations:
   ```bash
   ls -d "{vault}"/*Areas*/*/
   ls -d "{vault}"/*Resources*/*/
   ls -d "{vault}"/*Projects*/*/
   ```

2. For each note, extract signals (keywords, category, source)

3. Score each destination using the weighting table

4. Present using AskUserQuestion:
   - Option 1: Highest-scoring destination (if >50%)
   - Option 2: Second-highest (if >30%)
   - Option 3: Leave in Inbox

5. Execute move on selection:
   ```bash
   mv "{inbox}/{filename}" "{vault}/{selected-destination}/"
   ```
```

---

## Constraints

- **Never suggest non-existent paths** - Only paths from `ls` output
- **Always include inbox option** - Safe default for uncertain cases
- **Show reasoning** - Users should understand why
- **Two-level depth max** - Don't suggest `Area/Sub/Sub/Sub/`
- **Preserve filenames** - Don't rename when moving
- **Respect emoji prefixes** - Use exact folder names from filesystem
