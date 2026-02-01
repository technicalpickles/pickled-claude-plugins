# Note Routing System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add intelligent routing to second-brain plugin that discovers actual vault structure and suggests destinations with confidence levels and explanations.

**Architecture:** New routing reference (`references/routing.md`) defines the discovery and matching algorithm. Existing commands (`insight.md`, `distill-conversation.md`) are updated to use this reference. New standalone `route.md` command enables routing notes already in inbox.

**Tech Stack:** Markdown reference files, shell commands for vault discovery (find, grep)

---

## Task 1: Create Routing Reference

**Files:**
- Create: `plugins/second-brain/skills/obsidian/references/routing.md`

**Step 1: Create the routing reference file**

```markdown
# Note Routing Reference

How to route notes to the correct location in an Obsidian vault.

## Problem

Notes captured to inbox need routing to appropriate Projects/Areas/Resources locations. Routing must:
1. Only suggest destinations that **actually exist**
2. Provide **confidence levels** (High/Medium/Low)
3. Explain **why** each destination matches

## Phase 1: Structure Discovery

Before suggesting any routing, discover what actually exists in the vault.

### Step 1.1: Identify PARA Folders

PARA folders often have emoji prefixes. Find them:

```bash
# From vault root, find PARA top-level folders
ls -d */ | grep -E '(project|area|resource|archive)' -i
```

Common patterns:
- `1.🚀  Projects/` or `Projects/`
- `2.🏡 Areas/` or `Areas/`
- `3.📚  Resources/` or `Resources/`
- `4.📦  Archive/` or `Archive/`

### Step 1.2: Discover Subfolders

Get valid destinations (depth 2 max):

```bash
# For each PARA folder, list subfolders
find "{PARA_FOLDER}" -maxdepth 2 -type d 2>/dev/null
```

### Step 1.3: Build Destination Map

Create a mental map of valid destinations:

```
Projects:
  - gusto/ASYNC
  - gusto/karafka migration
  - personal website

Areas:
  - gusto
  - AI/agentic development
  - tool sharpening/vim
  - code-reviews/gusto

Resources:
  - software engineering
  - cocktails
  - obsidian
```

**CRITICAL:** Only suggest paths from this discovered map. Never hallucinate paths.

## Phase 2: Content Analysis

Extract signals from the note to match against destinations.

### Step 2.1: Extract Keywords

From note title and body, identify:
- **Primary topic:** Main subject (e.g., "Claude Code", "Redis", "vim")
- **Domain:** Work vs personal, technical vs non-technical
- **Action type:** Is it actionable? Has deadline? Ongoing?

### Step 2.2: Identify Signals

Strong signals (high weight):
- Explicit folder mentions ("put this in tool sharpening")
- Repo/project names that match folder names
- Tool/technology names matching Resources folders

Weak signals (low weight):
- General category (work, personal, technical)
- PARA category fit (actionable → Projects)

## Phase 3: Destination Matching

Score each discovered destination against the note.

### Step 3.1: Keyword Matching

For each destination folder:
- **Direct match:** Folder name contains note keyword → +40 points
- **Parent match:** Parent folder contains keyword → +20 points
- **Related notes:** Grep finds similar notes in folder → +30 points

### Step 3.2: PARA Category Fit

Apply PARA decision tree:
- Has deadline/deliverable? → Favor Projects (+10)
- Ongoing responsibility? → Favor Areas (+10)
- Reference material? → Favor Resources (+10)

### Step 3.3: Calculate Confidence

Sum scores for each destination:
- **High (70+ points):** Multiple strong signals align
- **Medium (40-69 points):** One strong signal or several weak ones
- **Low (20-39 points):** Best guess based on category
- **None (<20 points):** No match, recommend inbox

## Phase 4: Present Recommendations

Show top 3 destinations with explanations.

### Output Format

```
## Routing Analysis

**Note:** {note title}
**Keywords detected:** {keyword1}, {keyword2}
**PARA category:** {Projects|Areas|Resources}

### Recommendations

1. **{path}** - {confidence}% confidence
   - {explanation: why this matches}
   - Related notes: {existing notes found, if any}

2. **{path}** - {confidence}% confidence
   - {explanation}

3. **Leave in inbox**
   - No strong match found
   - Review manually when processing inbox
```

## Integration

Commands using this reference should:
1. Run Phase 1 once per session (cache discovered structure)
2. Run Phases 2-4 for each note being routed
3. Use AskUserQuestion to let user choose from recommendations
4. Move file to chosen destination if requested

## Example Routing

**Note:** "202601241430 redis-session-storage-pattern.md"
**Content:** Technical pattern about using Redis for session storage

**Analysis:**
- Keywords: redis, session, storage, pattern
- Domain: Technical, work-related
- PARA: Reference material (not actionable, not ongoing responsibility)

**Discovery found:**
- `Resources/software engineering/` exists
- `Areas/gusto/` exists (work area)
- `Resources/programming/` exists

**Scoring:**
1. `Resources/software engineering/` - 70%
   - "software engineering" matches technical content
   - Found 3 related architecture notes
2. `Areas/gusto/` - 45%
   - Work-related content
   - But this is reference, not ongoing responsibility
3. `Resources/programming/` - 40%
   - Generic programming match

**Recommendation:** Route to `Resources/software engineering/`
```

**Step 2: Verify file was created**

Run: `cat plugins/second-brain/skills/obsidian/references/routing.md | head -20`
Expected: Shows the header and Phase 1 start

**Step 3: Commit**

```bash
git add plugins/second-brain/skills/obsidian/references/routing.md
git commit -m "feat(second-brain): add routing reference for note destination matching

Defines algorithm for discovering vault structure and matching notes
to destinations with confidence levels and explanations."
```

---

## Task 2: Create Route Command

**Files:**
- Create: `plugins/second-brain/commands/route.md`

**Step 1: Create the route command file**

```markdown
---
description: Route a note from inbox to its proper location
argument-hint: [note path or title]
---

# Route Note

Route a note from inbox to its proper PARA location.

## Step 1: Load Configuration

Read `~/.claude/second-brain.md` for vault path.

If missing:
```
Second brain not configured. Run /second-brain:setup first.
```

Load references:
- `references/routing.md` for routing algorithm
- Vault's `CLAUDE.md` for structure

## Step 2: Identify Note to Route

**If argument provided:**
Use as note path or search term.

**If no argument:**
List recent notes in inbox:

```bash
# List recent inbox notes (last 10)
ls -t "{inbox_path}"/*.md | head -10
```

Use AskUserQuestion to let user select which note to route.

## Step 3: Discover Vault Structure

Follow `references/routing.md` Phase 1:

1. Find PARA folders (with their actual names/prefixes)
2. List subfolders to depth 2
3. Build map of valid destinations

Cache this for the session.

## Step 4: Analyze Note

Read the note content:

```bash
cat "{note_path}"
```

Follow `references/routing.md` Phase 2:
- Extract keywords from title and body
- Identify domain (work/personal, technical/non-technical)
- Determine PARA category fit

## Step 5: Match and Score

Follow `references/routing.md` Phase 3:

For each discovered destination:
1. Score keyword matches
2. Search for related notes:
   ```bash
   grep -l "{keyword}" "{destination}"/*.md 2>/dev/null | head -3
   ```
3. Apply PARA category bonus
4. Calculate confidence percentage

## Step 6: Present Recommendations

Show routing analysis per `references/routing.md` Phase 4 format:

```
## Routing Analysis

**Note:** {filename}
**Keywords:** {extracted keywords}
**PARA fit:** {category}

### Recommendations

1. **{path}** - {confidence}%
   → {explanation}
   → Related: {found notes or "none"}

2. **{path}** - {confidence}%
   → {explanation}

3. **Leave in inbox**
   → No strong match; review manually
```

Use AskUserQuestion with options:
1. {Top recommendation} (Recommended)
2. {Second recommendation}
3. Leave in inbox
4. Other (manual path)

## Step 7: Execute Routing

If user selects a destination:

```bash
# Move note to destination
mv "{inbox_path}/{filename}" "{destination_path}/{filename}"
```

Confirm:
```
✓ Moved to {destination_path}/{filename}
```

If "Leave in inbox" selected:
```
✓ Note remains in inbox for later routing
```

## Constraints

- **Only suggest existing paths** - Never hallucinate destinations
- **Show confidence levels** - Help user understand match quality
- **Explain reasoning** - Show why each destination matches
- **Respect user choice** - Don't auto-route without confirmation
```

**Step 2: Verify file was created**

Run: `cat plugins/second-brain/commands/route.md | head -20`
Expected: Shows frontmatter and Step 1

**Step 3: Commit**

```bash
git add plugins/second-brain/commands/route.md
git commit -m "feat(second-brain): add route command for inbox notes

Standalone command to route notes from inbox to PARA locations
with confidence-based recommendations."
```

---

## Task 3: Update Insight Command

**Files:**
- Modify: `plugins/second-brain/commands/insight.md:88-128` (Steps 6-7)

**Step 1: Read current insight.md**

Run: `cat plugins/second-brain/commands/insight.md`
Expected: See current Steps 6-7

**Step 2: Replace Steps 6-7 with routing reference usage**

Replace lines 88-128 (from "## Step 6: Confirm and Analyze" to end) with:

```markdown
## Step 6: Confirm Capture

After writing:
```
✓ Captured to inbox: {filename}
```

## Step 7: Route Using Algorithm

Load `references/routing.md` and follow the routing algorithm:

### 7.1: Discover Structure

Follow Phase 1 to find valid PARA destinations:
- Find actual PARA folder names (may have emoji prefixes)
- List subfolders to depth 2
- Build map of valid paths

### 7.2: Analyze Note

Follow Phase 2:
- Extract keywords from title and insight content
- Identify domain and PARA category fit

### 7.3: Score Destinations

Follow Phase 3:
- Score each destination by keyword match
- Search for related notes in candidate folders
- Calculate confidence percentages

### 7.4: Present Recommendations

Show routing analysis:

```
Analyzing for routing...

## Routing Analysis

**Keywords:** {extracted keywords}
**PARA fit:** {Projects|Areas|Resources}

### Recommendations

1. **{path}** - {confidence}%
   → {explanation}
   → Related: {found notes or "none"}

2. **{path}** - {confidence}%
   → {explanation}

3. **Leave in inbox**
   → No strong match; review manually
```

Use AskUserQuestion with routing options.

If user selects destination, move the file there and confirm.

## Constraints

- **Always write to inbox first** - Never skip this step
- **Use skill references** - Get paths from skill, not hardcoded
- **Zettelkasten naming** - Must use `YYYYMMDDHHMM title.md` format
- **Only suggest existing paths** - Use discovered structure, never hallucinate
- **Show confidence and reasoning** - Help user make informed choice
- **Clean prose** - Well-written insight, not raw conversation paste
```

**Step 3: Verify edit applied**

Run: `grep -n "routing.md" plugins/second-brain/commands/insight.md`
Expected: Shows references to routing.md

**Step 4: Commit**

```bash
git add plugins/second-brain/commands/insight.md
git commit -m "refactor(second-brain): use routing reference in insight command

Replaces ad-hoc routing with structured algorithm that:
- Discovers actual vault structure
- Provides confidence levels
- Explains recommendations"
```

---

## Task 4: Update Distill Command

**Files:**
- Modify: `plugins/second-brain/commands/distill-conversation.md:83-111` (Step 6)

**Step 1: Read current distill-conversation.md**

Run: `cat plugins/second-brain/commands/distill-conversation.md`
Expected: See current Step 6

**Step 2: Replace Step 6 with routing reference usage**

Replace lines 83-111 (from "## Step 6: Batch Routing" to end) with:

```markdown
## Step 6: Batch Routing

Load `references/routing.md` and apply to all captured notes.

### 6.1: Discover Structure Once

Follow Phase 1 to find valid PARA destinations.
Cache this for all notes in the batch.

### 6.2: Analyze Each Note

For each captured note, follow Phases 2-3:
- Extract keywords
- Score against destinations
- Calculate confidence

### 6.3: Present Batch Recommendations

```
## Routing Analysis

| Note | Recommendation | Confidence | Reason |
|------|---------------|------------|--------|
| {title1} | {path1} | {%} | {brief reason} |
| {title2} | {path2} | {%} | {brief reason} |
| {title3} | Leave in inbox | - | No strong match |
```

Use AskUserQuestion:

**Question:** "How should I route these?"

**Options:**
1. Route all as suggested (Recommended)
2. Route individually (I'll ask about each)
3. Leave all in inbox for now

### 6.4: Execute Routing

If "Route all as suggested":
- Move each note to its recommended destination
- Skip notes marked "Leave in inbox"
- Show summary of moves

If "Route individually":
- For each note, show full routing analysis
- Use AskUserQuestion for each
- Execute chosen routing

## Constraints

- **Be selective** - Only genuinely valuable insights
- **Categorize clearly** - Help user understand knowledge type
- **Batch efficiently** - Don't make user go through many dialogs
- **Only suggest existing paths** - Use discovered structure
- **Show confidence levels** - Help user trust recommendations
- **Clean prose** - Each insight standalone, useful months later
- **Zettelkasten naming** - Must use `YYYYMMDDHHMM title.md`
```

**Step 3: Verify edit applied**

Run: `grep -n "routing.md" plugins/second-brain/commands/distill-conversation.md`
Expected: Shows reference to routing.md

**Step 4: Commit**

```bash
git add plugins/second-brain/commands/distill-conversation.md
git commit -m "refactor(second-brain): use routing reference in distill command

Batch routing now uses structured algorithm with:
- Discovered vault structure (not hallucinated paths)
- Confidence levels in table format
- Explanations for each recommendation"
```

---

## Task 5: Update Skill Reference List

**Files:**
- Modify: `plugins/second-brain/skills/obsidian/SKILL.md:89-93`

**Step 1: Read current SKILL.md references section**

Run: `tail -10 plugins/second-brain/skills/obsidian/SKILL.md`
Expected: See references section

**Step 2: Add routing reference**

Add to the references list:

```markdown
## References

For methodology (tool-agnostic):
- `references/para.md` - PARA organizational system
- `references/zettelkasten.md` - Naming conventions
- `references/note-patterns.md` - Note templates
- `references/routing.md` - Note routing algorithm
```

**Step 3: Verify edit applied**

Run: `grep "routing.md" plugins/second-brain/skills/obsidian/SKILL.md`
Expected: Shows the new reference line

**Step 4: Commit**

```bash
git add plugins/second-brain/skills/obsidian/SKILL.md
git commit -m "docs(second-brain): add routing reference to skill

Lists routing.md in skill references for discoverability."
```

---

## Task 6: Integration Test

**Files:**
- Test: All modified files

**Step 1: Verify all files exist**

Run:
```bash
ls -la plugins/second-brain/skills/obsidian/references/routing.md
ls -la plugins/second-brain/commands/route.md
```
Expected: Both files exist

**Step 2: Verify references are linked**

Run:
```bash
grep -r "routing.md" plugins/second-brain/
```
Expected: Shows references in insight.md, distill-conversation.md, SKILL.md

**Step 3: Manual test (requires reinstall)**

To test in real Claude Code session:
```bash
/plugin uninstall second-brain@technicalpickles-marketplace
/plugin install second-brain@technicalpickles-marketplace
# Restart Claude Code
# Then: /second-brain:route
```

**Step 4: Final commit summary**

Run: `git log --oneline -5`
Expected: Shows the 5 commits from this plan
