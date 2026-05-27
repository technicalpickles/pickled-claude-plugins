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

Verify sb CLI is available and routing correctly:
```bash
npx @techpickles/sb --version
npm --version
```

If both return the same version (e.g., both `11.9.0`), `npx` is misdispatching to `npm` itself — an upstream npx bin-dispatch quirk seen intermittently. Subcommands will then fail with `npm error enoent Could not read package.json`. Fall back to direct-node invocation:

```bash
SB=$(ls ~/.npm/_npx/*/node_modules/@techpickles/sb/dist/index.js 2>/dev/null | head -1)
node "$SB" <subcommand>
```

If sb is not installed at all (`command not found` or hang):
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

Build one session note containing all selected insights as bullets, then write it via `sb note create`. The CLI has no `note list` subcommand and `note create` has no `--type` flag, so don't try to "find or create" a per-session file by type — render the content first and create the note once.

**5a. Build session context:**

Collect for the `--source` provenance string:
- Current repo (if in a worktree)
- Current branch (if in a worktree)
- Current bean ID (if applicable)
- Short session id (first 8 chars of the session UUID)

Format: `claude-code session {short-id} ({repo}, branch {branch}, bean {id})`

**5b. Render bullets:**

For each selected insight, write a clean prose bullet:
- Standalone (readable months later without conversation context)
- One short paragraph per insight
- Format: `- **{name}**: {description}`

Stage the full content (optional framing paragraph + bullets) in a temp file:

```bash
cat > "$TMPDIR/distill-content.txt" <<'EOF'
{optional framing paragraph}

- **{name}**: {description}
- **{name}**: {description}
EOF
```

A temp file is preferred over inlining `--content "..."` because heredoc-quoted content avoids shell escaping bugs on multi-line markdown.

**5c. Create the note:**

```bash
npx @techpickles/sb note create \
  --title "Session: {topic}" \
  --source "{session-context-string}" \
  --content "$(cat "$TMPDIR/distill-content.txt")"
```

Parse the returned JSON for the `path` field; show it in the confirmation.

**5d. Sandbox EPERM on vault writes:**

Vault paths like `~/.claude/vaults/primary` symlink into directories outside Claude Code's sandbox writeable allowlist. The first `sb note create` against the vault in a session will fail with:

```
Error: EPERM: operation not permitted, open '/path/to/vault/📫 Inbox/...'
```

This is not an sb bug — retry the same command with the Bash tool's `dangerouslyDisableSandbox: true` option. Subsequent vault writes in the same session usually succeed without retry.

**5e. Confirm:**

```
✓ Captured {N} insights to {filename}
```

The note lands in the vault inbox and will be routed / connected / daily-linked by the next `/second-brain:process-inbox` run.

## Constraints

- **Be selective** - Only genuinely valuable insights
- **Categorize clearly** - Help user understand knowledge type
- **Clean prose** - Each insight standalone, useful months later
- **Metadata included** - Capture repo, branch, bean, session topic for context
- **Processing deferred** - Routing, connecting, and daily linking happen later via `/second-brain:process-inbox`
