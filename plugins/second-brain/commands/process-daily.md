---
description: Process voice transcriptions in today's daily note
argument-hint: [date, e.g. 2026-01-21]
---

# Process Daily Note

Clean up voice transcriptions in a daily note. Works in phases with confirmation between each.

## Prerequisite: Vault Context Check

**This command only works inside a vault.**

Check if current directory is a vault:

```bash
ls -d .obsidian 2>/dev/null
```

If `.obsidian/` not found in current directory or parents:

```
⚠ /second-brain:process-daily only works inside a vault.

You're currently in: {cwd}

Options:
1. Open your vault: {path from ~/.claude/second-brain.md}
2. Use /second-brain:insight to capture from here
3. Use /second-brain:distill-conversation for end-of-session extraction
```

Stop execution - do not continue.

## Overview (when in vault)

1. Load context (daily note, glossary, vault conventions)
2. Identify & confirm transcription corrections (batched by category)
3. Clean prose (preview before applying)
4. Restructure to daily note template (preview before applying)
5. Suggest extractions (optional)

## Phase 1: Load Context

### Step 1.1: Read Vault CLAUDE.md

Read `CLAUDE.md` at vault root for:
- Daily note location
- Template reference
- Structure conventions

### Step 1.2: Find the Daily Note

**If argument provided:** Use as date (parse YYYY-MM-DD format)
**If no argument:** Use today's date

```bash
date +"%Y-%m-%d"
```

Construct path from vault's daily note location (e.g., `Fleeting/{date}.md`).

If file doesn't exist, inform user and stop.

### Step 1.3: Load Glossary

Read `Glossary.md` if it exists at vault root.

Parse correction mappings by category.

### Step 1.4: Assess Content

Read daily note. Report:
```
Loaded: Fleeting/2026-01-21.md
Glossary: Found ({N} known corrections)
Content: ~{N} words, {structured|unstructured}

Ready to process. Continue? [Yes] [Cancel]
```

## Phase 2: Identify & Confirm Corrections

Present corrections in batches by category:

```
### Tools & Software (Batch 1 of 4)

| # | Found | → Correction | Context |
|---|-------|--------------|---------|
| 1 | me's | mise | "started using me's" |
| 2 | Claude MT | CLAUDE.md | "added Claude MT" |

✓ Accept all | Enter numbers to reject | ? for more context
```

Categories:
1. Known corrections (from Glossary) - batch accept
2. Tool/product names
3. People names
4. Technical terms
5. Uncertain - need user input

After all batches, offer glossary update for new corrections.

## Phase 3: Clean Prose

Remove filler words, false starts, run-on sentences.

Preserve: conversational tone, first-person voice, meaning.

Show before/after preview for representative sections.

## Phase 4: Restructure (if needed)

If note lacks structure, propose restructuring to match daily template:

```
## Action Items    ← Top: high visibility
## Extracted Notes ← Links to permanent notes
## Log             ← Structured events
## Quick Notes     ← Bottom: append zone
```

## Phase 5: Suggest Extractions

Identify content substantial enough for permanent notes.

Criteria: substantial, reusable, standalone, reference-worthy.

Offer extraction with routing.

## Constraints

- **Vault-only** - Must be run from inside vault
- **Interactive** - Always preview before applying
- **Batch confirmations** - Group similar items
- **Preserve meaning** - Never change what was said
- **Follow skill references** - Use vault conventions
- **Phases skippable** - User can skip any phase
