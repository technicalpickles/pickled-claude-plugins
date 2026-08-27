# Second Brain Plugin

Knowledge management for Obsidian vaults. Capture insights from conversations, process voice transcriptions, and connect repos to your vault.

## Installation

Requires the [pickled-claude-plugins marketplace](../../README.md#installation). Then:

```bash
/plugin install second-brain@pickled-claude-plugins
```

## Quick Start

1. **Configure your vault:**
   ```
   /second-brain:setup
   ```
   This detects your Obsidian settings and creates `~/.claude/second-brain.md`.

2. **Capture an insight:**
   ```
   /second-brain:insight Redis is better than Memcached for sessions because it supports TTL per key
   ```
   Writes to your vault's inbox with provenance (repo, branch, commit).

3. **Devlog runs on its own:**
   No command to run. `devlog` writes a point-in-time entry to the
   current session's note whenever you finish something notable — a
   feature, a bug fix, a gotcha worth remembering. Nothing to remember,
   nothing to invoke.

## Commands

| Command | Description | Works From |
|---------|-------------|------------|
| `/second-brain:setup` | Configure vault path, detect settings | Anywhere |
| `/second-brain:insight` | Capture single insight to inbox | Anywhere |
| `/second-brain:process-daily` | Clean voice transcriptions in daily note | Vault only |
| `/second-brain:link-project` | Symlink repo folder to vault | Any repo |

## Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                     Any Repository                          │
│                                                             │
│  Working on code...                                         │
│  ↓                                                          │
│  /second-brain:insight "key learning"                       │
│  ↓                                                          │
│  Writes to vault inbox with repo/branch/commit context      │
│                                                             │
│  Finished something notable...                              │
│  ↓                                                          │
│  devlog writes an entry automatically, no command needed    │
│  ↓                                                          │
│  Later: /second-brain:process-inbox routes, connects, links │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Inside Vault                             │
│                                                             │
│  Voice transcription in daily note...                       │
│  ↓                                                          │
│  /second-brain:process-daily                                │
│  ↓                                                          │
│  1. Correct transcription errors (batched)                  │
│  2. Clean prose (preview before applying)                   │
│  3. Restructure to template                                 │
│  4. Suggest extractions to permanent notes                  │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### Global: `~/.claude/second-brain.md`

Created by `/second-brain:setup`:

```markdown
# Second Brain Configuration

## Vaults

- primary: ~/Vaults/my-vault/

Default: primary
```

### Vault Symlinks: `~/.claude/vaults/`

Setup creates symlinks at `~/.claude/vaults/{name}` pointing to actual vault paths. This provides predictable paths for permissions and access:

```bash
~/.claude/vaults/primary -> ~/Vaults/my-vault/
```

### Vault: `{vault}/CLAUDE.md`

Scaffolded by setup command with detected settings:
- Folder structure (inbox, daily notes, templates)
- Routing rules (PARA-based)
- Naming conventions (Zettelkasten)

### Project: `.claude/second-brain.local.md`

Created by `/second-brain:link-project`:

```markdown
# Second Brain Connection

Vault: primary

Symlinks:
- docs/notes/ → Areas/my-project/
```

## Skills & References

### `capture` — read a source, write a note

The front door for "read this and make a note for it." Runs the whole loop as one arc so no step
gets silently skipped:

1. **Search first** via the qmd MCP tools, showing what already exists before anything is written
2. **Read the primary source** (lightpanda / WebFetch / xtweet / Read / Notion), never a snippet
3. **Create through `sb note create`**, which owns the inbox path, timestamp, and filename slug
4. **Leave it in the inbox** — routing is offered, not performed
5. **Offer connections** plus a daily-note breadcrumb

Also handles "do we have a note about X already?" lookups, including the recall fallbacks for when
semantic search misses (basename search across the vault, checking both inbox folders).

| Reference | Content |
|-----------|---------|
| `skills/capture/references/note-format.md` | Frontmatter and body shape for a fresh capture |

### `obsidian` — vault mechanics

| Reference | Content |
|-----------|---------|
| `references/para.md` | PARA methodology (Projects, Areas, Resources, Archive) |
| `references/zettelkasten.md` | Timestamp naming convention |
| `references/note-patterns.md` | Templates for person, meeting, insight, investigation notes |
| `references/sb-cli.md` | The `sb` CLI command surface |

## Note Format

Insights are captured with provenance:

```markdown
---
captured: 2026-01-21T14:30:00Z
source: claude-conversation
repo: my-project
branch: feature/auth
commit: abc1234
---

# Redis Over Memcached for Sessions

Redis supports per-key TTL, making it better suited for session storage
where different sessions may have different expiration requirements.

## Context

Captured while debugging session expiration issues in the auth system.

---
*Captured via /second-brain:insight*
```

## License

MIT
