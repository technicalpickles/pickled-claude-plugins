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

Verify sb CLI is available and routing correctly, and load configuration, in one round-trip:
```bash
npx @techpickles/sb --version && npm --version
npx @techpickles/sb config default && npx @techpickles/sb config vaults
```

If the two `--version` outputs are identical (e.g., both `11.9.0`), `npx` is misdispatching to `npm` itself — an upstream npx bin-dispatch quirk seen intermittently. Subcommands will then fail with `npm error enoent Could not read package.json`. Fall back to direct-node invocation:

```bash
SB=$(ls ~/.npm/_npx/*/node_modules/@techpickles/sb/dist/index.js 2>/dev/null | head -1)
node "$SB" <subcommand>
```

If sb is not installed at all (`command not found` or hang):
```
sb CLI is required but not available. Install Node.js and npm, then try again.
Or install globally for faster execution: npm i -g @techpickles/sb
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

Build one session note containing all selected insights as bullets, then write it via `sb note create`. `note create` has no `--type` flag, so don't try to "find or create" a per-session file by type — render the content first and create the note once.

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

**5c. Stage and create the note in one Bash call, sandbox disabled from the start:**

Stage the full content (optional framing paragraph + bullets) in a `mktemp`-generated file and immediately read it back for `sb note create`, all in the same Bash tool call, with the Bash tool's `dangerouslyDisableSandbox: true` option set on that call from the start:

```bash
STAGE=$(mktemp)
cat > "$STAGE" <<'EOF'
{optional framing paragraph}

- **{name}**: {description}
- **{name}**: {description}
EOF
npx @techpickles/sb note create \
  --title "Session: {topic}" \
  --source "{session-context-string}" \
  --content "$(cat "$STAGE")"

rm -f "$STAGE"
```

Run it unsandboxed from the start rather than trying sandboxed first and retrying on failure, for two reasons:

- Vault paths like `~/.claude/vaults/primary` symlink into directories outside Claude Code's sandbox writeable allowlist, so a sandboxed attempt always fails with `Error: EPERM: operation not permitted, open '/path/to/vault/📫 Inbox/...'` — not an sb bug, just a guaranteed wasted round-trip if you wait for it.
- `$TMPDIR` resolves to a *different path* under `dangerouslyDisableSandbox: true` than under the normal sandbox. Staging and reading in the same call under the same sandbox mode keeps them pointed at the same directory — splitting them across calls or sandbox modes can read a stale file from a different session, or fail to find the one just written.

A staged file is preferred over inlining `--content "..."` because heredoc-quoted content avoids shell escaping bugs on multi-line markdown. It must be a fresh `mktemp` path, not a fixed filename: `$TMPDIR` is shared across every Claude Code session on the machine, and a fixed-name file (e.g. `$TMPDIR/distill-content.txt`) can be overwritten or read by a stale write from a different session.

Parse the returned JSON for the `path` field; show it in the confirmation. If stdout has anything before the `{` (e.g. an `npm warn ...` line from the caller's own `.npmrc`), extract the JSON substring starting at the first `{` rather than parsing the whole stdout blob.

**5d. Confirm:**

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
