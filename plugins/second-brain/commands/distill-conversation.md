---
description: Extract and capture multiple insights from this conversation
---

# Distill Conversation

Review the current conversation and extract insights worth capturing.

## Step 1: Load Configuration

Read `~/.claude/second-brain.md` for vault path.

If missing:
```
Second brain not configured. Run /second-brain:setup first.
```

Load skill references for note patterns and naming.

## Step 2: Review the Conversation

Scan through the conversation looking for:

1. **Architecture decisions** - Choices about design, technology, structure
2. **Debugging patterns** - Root causes found, diagnostic approaches
3. **Domain knowledge** - Business logic, system behavior
4. **Process improvements** - Better ways of doing things
5. **Key learnings** - Surprising findings, corrected misunderstandings

## Step 3: Present Findings

Show what you found:

```
Reviewing this conversation...

Found {N} potential insights worth capturing:

1. **{Category}**: {Brief description}
   → {Why this might be worth keeping}

2. **{Category}**: {Brief description}
   → {Why this might be worth keeping}

3. **{Category}**: {Brief description}
   → {Why this might be worth keeping}
```

If nothing worth capturing:
```
Reviewed this conversation - no notable insights to capture.
The conversation was mostly {operational/routine/exploratory without conclusions}.
```

## Step 4: Let User Select

Use AskUserQuestion with multi-select enabled:

**Question:** "Which insights should I capture?"

**Options:** List each insight (up to 4, mention others)

Include "None - skip capture" option.

## Step 5: Capture Selected

For each selected insight, follow `/second-brain:insight` flow:
1. Gather provenance
2. Generate Zettelkasten filename
3. Write to inbox with Insight Note pattern
4. Show confirmation

```
Capturing {N} insights...

✓ {filename1}
✓ {filename2}
✓ {filename3}

All captured to inbox.
```

## Step 6: Batch Routing

Analyze captured notes:

```
Analyzing captured notes for routing...

1. "{insight1}" → looks like it belongs in {suggested path}
2. "{insight2}" → looks like it belongs in {suggested path}
3. "{insight3}" → no clear match, recommend leaving in inbox
```

Use AskUserQuestion:

**Question:** "How should I route these?"

**Options:**
1. Route all as suggested
2. Route individually (I'll ask about each)
3. Leave all in inbox for now

## Constraints

- **Be selective** - Only genuinely valuable insights
- **Categorize clearly** - Help user understand knowledge type
- **Batch efficiently** - Don't make user go through many dialogs
- **Clean prose** - Each insight standalone, useful months later
- **Zettelkasten naming** - Must use `YYYYMMDDHHMM title.md`
