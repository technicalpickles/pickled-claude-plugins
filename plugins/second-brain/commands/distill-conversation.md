---
description: Extract and capture multiple insights from this conversation
allowed-tools:
  - Read(~/.claude/vaults/**/CLAUDE.md)
  - Read(~/.claude/vaults/**/.obsidian/*.json)
  - Read(~/.claude/vaults/**/*.md)
  - Write(~/.claude/vaults/**/*.md)
  - Edit(~/.claude/vaults/**/*.md)
  - Bash(npx @techpickles/sb:*)
---

# Distill Conversation

Review the current conversation and extract insights worth capturing.

## Step 1: Load Configuration

Verify sb CLI is available:
```bash
npx @techpickles/sb --version
```

If unavailable:
```
sb CLI is required but not available. Install Node.js and npm, then try again.
Or install globally for faster execution: npm i -g @techpickles/sb
```

Load configuration via sb:
```bash
npx @techpickles/sb config default
npx @techpickles/sb config vaults
```

If no default vault configured:
```
Second brain not configured. Run /second-brain:setup first.
```

Use the symlink path `~/.claude/vaults/{name}` to Read vault files (e.g., `~/.claude/vaults/primary/CLAUDE.md`).

Load skill references:
- `second-brain:obsidian` for tool mechanics
- `references/sb-cli.md` for sb command patterns
- `references/zettelkasten.md` for naming
- `references/note-patterns.md` for note template patterns

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

For each selected insight, append as a bullet to the session notes file.

**5a. Get or create session notes file:**

Check if a session file exists in the vault by querying sb:
```bash
npx @techpickles/sb note list --type session-notes
```

If none exists, create one with session context:
```bash
npx @techpickles/sb note create \
  --source auto \
  --title "{session context}" \
  --type session-notes
```

Parse the returned JSON to get the file path.

**5b. Build metadata:**

Collect session context:
- Current repo (if in a worktree)
- Current branch (if in a worktree)
- Current bean ID (if available from context)
- Session topic (topic of conversation)
- Timestamp (ISO 8601)

**5c. Append insights as bullets:**

For each selected insight, append a clean bullet point:
- Keep prose concise and standalone
- Include minimal metadata as needed (source, why this matters)
- Format: `- {insight description}` or `- {insight description} ({context})`

Use the Write tool to update the session file, preserving frontmatter and adding bullets to the content.

**5d. Confirm:**

```
✓ Captured {N} insights to {session-file}
```

Show the file path so user can find the notes later.

## Constraints

- **Be selective** - Only genuinely valuable insights
- **Categorize clearly** - Help user understand knowledge type
- **Clean prose** - Each insight standalone, useful months later
- **Metadata included** - Capture repo, branch, bean, session topic for context
- **Processing deferred** - Routing, connecting, and daily linking happen later via `/second-brain:process-inbox`
