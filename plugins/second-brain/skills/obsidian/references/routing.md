# Note Routing Reference

Systematic algorithm for discovering vault structure and matching notes to destinations.

**Key principle:** Vault-specific disambiguation rules take precedence over generic matching. Always check the vault's CLAUDE.md for routing guidance before scoring.

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

## Step 3: Load Vault Disambiguation Rules

Read the vault's `CLAUDE.md` file and look for disambiguation sections.

### Locate Disambiguation Sections

Search for headers matching `### Disambiguation:` pattern:

```markdown
### Disambiguation: tool sharpening vs software engineering
### Disambiguation: Areas vs Resources
```

### Extract Decision Criteria

For each disambiguation section, extract:

1. **Area definitions** - What belongs in each area
   - Look for `#### {area-name}` subheaders
   - Extract category tables and examples

2. **Key questions** - Decision heuristics
   - Pattern: `**Key question:** "..."`
   - These are the primary decision criteria

3. **Edge case mappings** - Explicit routing rules
   - Look for tables with `| Scenario | Route to | Reasoning |`
   - These override generic matching

### Example Disambiguation Structure

```markdown
### Disambiguation: tool sharpening vs software engineering

#### tool sharpening (MY workflow)
Notes about tools I configure for **personal productivity**...
| Category | Examples |
|----------|----------|
| Terminal/shell | tmux, ghostty, fish, zsh |
| CLI utilities | fzf, ripgrep, jq |

**Key question:** "Is this about how I set up MY machine?"

#### software engineering (project ecosystem)
Notes about tools tied to **language ecosystems**...
| Category | Examples |
|----------|----------|
| Ruby ecosystem | rake, bundler, rubocop |
| Build/CI tools | make, docker (for projects) |

**Key question:** "Is this about how projects/codebases work?"

#### Edge cases
| Scenario | Route to | Reasoning |
|----------|----------|-----------|
| tmux config syntax | tool sharpening | MY terminal setup |
| git aliases | tool sharpening | MY git workflow |
| docker multi-stage builds | software engineering | Project patterns |
```

### If No Disambiguation Rules Found

Proceed to Step 4 with generic matching only. The vault owner hasn't defined semantic boundaries yet.

---

## Step 4: Match Destinations

Score each discovered destination against the note using both generic signals and vault-specific rules.

### 4a: Apply Disambiguation Rules First

If disambiguation rules were loaded in Step 3:

1. **Check edge case mappings** - Does the note match an explicit rule?
   - If yes: That destination gets +50% boost, others in the disambiguation get -20%
   - Example: "tmux config" explicitly maps to "tool sharpening" → boost that destination

2. **Apply key questions** - Which area's key question does the note answer?
   - "Is this about how I set up MY machine?" → boost tool sharpening
   - "Is this about how projects/codebases work?" → boost software engineering

3. **Check category tables** - Does the note's tool/topic appear in a category list?
   - "fzf" in tool sharpening's CLI utilities → boost tool sharpening
   - "rubocop" in software engineering's Ruby ecosystem → boost software engineering

### 4b: Generic Signal Scoring

Apply baseline scoring to all destinations:

| Signal | Weight | Description |
|--------|--------|-------------|
| Keyword in folder name | 40% | Direct match: "claude" in title → "AI/agentic development/" |
| Related notes in folder | 30% | Grep for similar terms in destination folder |
| PARA category fit | 20% | Is this ongoing (Area), reference (Resource), or active (Project)? |
| Recency | 10% | Recently modified files in folder suggest active use |

### 4c: Combine Scores

Final score = Generic score + Disambiguation adjustments

- Edge case match: +50% to matched destination
- Key question match: +25% to matched destination
- Category table match: +15% to matched destination
- Disambiguation mismatch: -20% (when another area in the disambiguation is preferred)

### Matching Examples

**Note:** `202601281225 tmux conditional comma parsing conflict.md`
- Keywords: "tmux", "conditional", "parsing"
- Category: Tool configuration

**Without disambiguation:**
- `Resources/programming/` → 55% (tmux is programming-adjacent)
- `Areas/tool sharpening/` → 45% (keyword partial match)

**With disambiguation rules:**
- Edge case: "tmux config syntax → tool sharpening" matches → +50%
- Key question: "Is this about MY machine?" → Yes → +25%
- Final: `Areas/tool sharpening/` → 120% (capped at 95%)
- Final: `Resources/programming/` → 35% (disambiguation mismatch: -20%)

---

## Step 5: Confidence Levels

| Level | Score | Interpretation |
|-------|-------|----------------|
| **High** | 80-100% | Strong match, often with disambiguation rule support |
| **Medium** | 50-79% | Partial match or category-only fit |
| **Low** | 20-49% | Weak signals, might fit |
| **None** | <20% | No meaningful match - leave in inbox |

### When to Recommend Inbox

- No destination scores above 20%
- Multiple destinations score equally (unclear fit)
- Note is too generic to categorize
- User should decide after more context emerges
- Disambiguation rules conflict (both areas seem valid)

---

## Step 6: Present with Explanations

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

When disambiguation rules influenced the result:
```
1. **Areas/tool sharpening/** (95% - High)
   → Vault rule: "tmux config syntax" → tool sharpening
   → Key question: "Is this about MY machine?" → YES
```

### Presentation Rules

- Show top 2-3 destinations (not all)
- Include confidence level and percentage
- Explain WHY each destination matched
- Note when disambiguation rules applied
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

3. Load disambiguation rules from vault CLAUDE.md:
   - Read {vault}/CLAUDE.md
   - Find `### Disambiguation:` sections
   - Extract key questions, category tables, edge cases

4. Score each destination:
   - Apply disambiguation rules first (edge cases → key questions → categories)
   - Then apply generic signal weights
   - Combine scores with adjustments

5. Present using AskUserQuestion:
   - Option 1: Highest-scoring destination (if >50%)
   - Option 2: Second-highest (if >30%)
   - Option 3: Leave in Inbox
   - If disambiguation rule applied, note it in the explanation

6. Execute move on selection:
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

---

## Building Disambiguation Rules

Vault owners can add disambiguation rules to their `CLAUDE.md` to improve routing accuracy for semantically similar areas.

### When to Add Disambiguation Rules

Add rules when:
- Two areas have overlapping topics (e.g., "tool sharpening" vs "software engineering")
- Notes frequently get misrouted to similar-sounding destinations
- You have a clear mental model that keywords alone don't capture

### Disambiguation Section Format

```markdown
### Disambiguation: {area1} vs {area2}

Brief description of when this disambiguation applies.

#### {area1} ({context hint})

Notes about [what belongs here].

| Category | Examples |
|----------|----------|
| {category1} | {tool1}, {tool2}, {tool3} |
| {category2} | {tool4}, {tool5} |

**Key question:** "{Question that, if answered YES, means route here}"

#### {area2} ({context hint})

Notes about [what belongs here].

| Category | Examples |
|----------|----------|
| {category1} | {tool1}, {tool2} |

**Key question:** "{Question that, if answered YES, means route here}"

#### Edge cases

| Scenario | Route to | Reasoning |
|----------|----------|-----------|
| {specific example} | {destination} | {why} |
| {specific example} | {destination} | {why} |
```

### Key Question Design

Good key questions are:
- **Mutually exclusive** - Only one should answer YES for a given note
- **Concrete** - About observable properties, not abstract qualities
- **Simple** - Can be answered quickly by examining the note

| Good | Bad |
|------|-----|
| "Is this about how I set up MY machine?" | "Is this technical?" |
| "Is this about how projects/codebases work?" | "Is this important?" |
| "Does this have a deadline?" | "Should I remember this?" |

### Edge Case Table Design

Use edge cases for:
- **Ambiguous tools** - Tools that appear in multiple contexts (git, docker)
- **Common confusions** - Topics you've seen misrouted before
- **Exceptions** - Cases where the key question gives the wrong answer

```markdown
#### Edge cases

| Scenario | Route to | Reasoning |
|----------|----------|-----------|
| git aliases, config | tool sharpening | MY git workflow |
| git concepts, branching strategies | software engineering | How git works |
| docker cleanup commands | tool sharpening | Local machine maintenance |
| docker multi-stage builds | software engineering | Project patterns |
```

### Category Table Design

Category tables help with keyword matching:

```markdown
| Category | Examples |
|----------|----------|
| Terminal/shell | tmux, ghostty, kitty, fish, zsh |
| CLI utilities | fzf, ripgrep, jq, yq, fd, bat |
```

Tips:
- List **specific tool names** - These become keywords
- Group by **function** - Helps you think systematically
- Include **common variations** - "vim", "neovim", "nvim"

### Testing Your Rules

After adding disambiguation rules:

1. Review recent captures that were misrouted
2. Run `/second-brain:route` on a test note
3. Check if the explanation mentions your disambiguation rule
4. Adjust key questions or edge cases if routing is still wrong

### Evolving Rules Over Time

- **Start minimal** - Add rules only when you see misrouting
- **Be specific** - Vague rules don't help
- **Update edge cases** - As you encounter new ambiguities
- **Remove unused rules** - If areas become clearly distinct
