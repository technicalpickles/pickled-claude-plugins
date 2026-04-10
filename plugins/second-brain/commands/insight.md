---
description: Capture an insight from conversation to your second brain
argument-hint: [insight to capture]
allowed-tools:
  - Read(~/.claude/vaults/**/CLAUDE.md)
  - Read(~/.claude/vaults/**/.obsidian/*.json)
  - Read(~/.claude/vaults/**/*.md)
  - Write(~/.claude/vaults/**/*.md)
  - Edit(~/.claude/vaults/**/*.md)
  - Bash(npx @techpickles/sb:*)
---

# Capture Insight

Capture an insight from the current conversation to your Obsidian vault inbox.

This command captures raw insights quickly. Processing, routing, and connection discovery happen later via `/second-brain:process-inbox`.

## Step 1: Load Configuration

Load configuration using sb CLI:

```bash
npx @techpickles/sb config default    # Get default vault name
npx @techpickles/sb config vaults     # List all configured vaults
```

If sb is not available, inform user:
```
sb CLI is required but not available. Install Node.js and npm, then try again.
Or install globally for faster execution: npm i -g @techpickles/sb
```

If no vaults are configured, inform user:
```
Second brain not configured. Run /second-brain:setup first.
```

Use the symlink path `~/.claude/vaults/{name}` to access the vault for reading CLAUDE.md (e.g., `~/.claude/vaults/primary`).

Read vault's `CLAUDE.md` for structure rules.

Load skill references:
- `second-brain:obsidian` for tool mechanics
- `references/sb-cli.md` for sb invocation details
- `references/zettelkasten.md` for naming

## Step 2: Identify the Insight

**If argument provided:**
Use the argument as the insight to capture.

**If no argument:**
Ask: "What insight would you like to capture?"

Also review recent conversation context to suggest what might be worth capturing.

## Step 3: Create or Append to Session Notes

Session notes files collect all insights from a conversation in one place, with cheap metadata attached at capture time.

**Check if session file already exists in this conversation.**

If this is the first `/insight` command in this conversation:
1. Create a new session notes file using sb CLI:
```bash
npx @techpickles/sb note create \
  --source auto \
  --title "{session context}"
```

Generate the title from conversation context: repo name, current branch, bean ID if available, and what you're working on (e.g., "Debugging auth timeout in zenpayroll").

The file is created with frontmatter. Read the created file to preserve the exact frontmatter sb wrote.

Add `type: session-notes` to the frontmatter if not present. The frontmatter should include:
- `status: raw`
- `type: session-notes`
- `source-session: {topic}`
- `repo: {repo-name}` (from git context if available)
- `branch: {branch-name}` (from git context if available)
- `bean: {bean-id}` (from git context if available)
- `captured: {ISO timestamp}`

Then write the note structure:

```markdown
---
status: raw
type: session-notes
source-session: {topic}
repo: {repo-name}
branch: {branch-name}
bean: {bean-id}
captured: {ISO timestamp}
---

# Session: {Session Title}

- {Insight bullet 1}
```

Use Write tool with the file content.

**If session file already exists** (was created in an earlier `/insight` call in this same conversation):
1. Append the new insight as a bullet using Edit tool
2. Insert under the bulleted list in the session notes file
3. Write the insight as clean prose (1-3 words to a sentence, not raw conversation)

Example:
```markdown
- Redis TTL per-key is better than Memcached for sessions
- Auth timeout varies by environment: 30s prod, 2m staging, 10m dev
```

## Confirm Capture

After creating or appending, confirm with one line:
```
Captured to inbox: {filename}
```

That's it. No routing, no connecting, no daily linking. Those happen later via `/second-brain:process-inbox`.

## Constraints

- **Always write to inbox** - Inbox capture only, no routing
- **Use sb CLI for note creation** - sb handles timestamps, frontmatter, vault structure
- **Capture cheap metadata** - repo, branch, bean ID from git/provenance context
- **Clean prose for bullets** - Each insight is a polished sentence or short phrase
- **No routing, connecting, or linking** - Processing moves to the separate `process-inbox` skill
