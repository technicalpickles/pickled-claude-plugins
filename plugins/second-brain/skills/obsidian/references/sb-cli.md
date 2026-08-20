# sb CLI Reference

The second-brain plugin uses `sb` for vault data operations (note creation, moving, config, structure discovery). This file defines how to invoke it.

## Invocation

```bash
npx @techpickles/sb <command> [options]
```

All sb commands output JSON for structured parsing.

## Don't Preflight-Check Availability

Don't run `sb --version` (or similar) before the "real" sb call in a flow just to
confirm sb is there. Call the command you actually need; sb is reliably available via
npx. Spending a turn on a speculative availability check on every flow, on the
overwhelming-common happy path, is wasted work.

If an sb call does fail, run the bundled diagnostic in one shot instead of re-deriving
the checks by hand:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/diagnose-sb.sh
```

It reports whether sb is missing, whether npx is misdispatching to npm (a known but
long-dormant bin-dispatch quirk), and the working fallback invocation if so. Show its
output to the user rather than re-implementing the same checks inline.

## Commands

### Configuration
- `npx @techpickles/sb config vaults` - list configured vaults as JSON
- `npx @techpickles/sb config default` - get default vault name
- `npx @techpickles/sb config qmd-collection` - qmd collection name for semantic search

### Vault
- `npx @techpickles/sb vault info` - vault metadata
- `npx @techpickles/sb vault obsidian` - parse .obsidian config as JSON
- `npx @techpickles/sb vault structure` - discover routable destinations (PARA and/or Johnny Decimal) as JSON, each tagged with a `type`

### Notes
- `npx @techpickles/sb note create --source auto --title "..."` - create note scaffold in inbox (frontmatter + heading, returns path as JSON)
- `npx @techpickles/sb note create --source auto --title "..." --content "..."` - create note with body (use for short content only)
- `npx @techpickles/sb note create --source auto --title "..." --dry-run` - preview without writing
- `npx @techpickles/sb note read --note "path/to/note.md"` - parse note as structured JSON
- `npx @techpickles/sb note context --note "path/to/note.md"` - routing context (keywords, category, related notes)
- `npx @techpickles/sb note move --from "inbox/note.md" --to "Areas/topic/"` - move note to destination

### Daily Notes
- `npx @techpickles/sb daily path` - today's daily note path
- `npx @techpickles/sb daily append --section "Links" --content "- [[note]]"` - append to daily note section

### Inbox
- `npx @techpickles/sb inbox list` - list inbox notes (lightweight: filename, timestamp, title)
- `npx @techpickles/sb inbox list --detail` - with parsed frontmatter

### Setup
- `npx @techpickles/sb init --name "..." --path "..."` - initialize vault configuration
- `npx @techpickles/sb init --name "..." --path "..." --scaffold` - also create vault CLAUDE.md
- `npx @techpickles/sb permissions` - generate Claude Code permission entries for vault
- `npx @techpickles/sb permissions --vault "name"` - for a specific vault

### Context
- `npx @techpickles/sb provenance` - git context (repo, branch, commit) as JSON
- `npx @techpickles/sb describe <command>` - runtime schema introspection
