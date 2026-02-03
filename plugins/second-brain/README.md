# Second Brain Plugin

Knowledge management for Obsidian vaults. Capture insights from conversations, process voice transcriptions, and connect repos to your vault.

## Installation

```bash
claude plugin add pickled-claude-plugins/second-brain
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

3. **End-of-session extraction:**
   ```
   /second-brain:distill-conversation
   ```
   Reviews the conversation and offers to capture multiple insights.

## Commands

| Command | Description | Works From |
|---------|-------------|------------|
| `/second-brain:setup` | Configure vault path, detect settings | Anywhere |
| `/second-brain:insight` | Capture single insight to inbox | Anywhere |
| `/second-brain:distill-conversation` | Extract multiple insights from conversation | Anywhere |
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
│  End of session...                                          │
│  ↓                                                          │
│  /second-brain:distill-conversation                         │
│  ↓                                                          │
│  Extracts all valuable insights, routes to proper locations │
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

The plugin includes an `obsidian` skill with:

| Reference | Content |
|-----------|---------|
| `references/para.md` | PARA methodology (Projects, Areas, Resources, Archive) |
| `references/zettelkasten.md` | Timestamp naming convention |
| `references/note-patterns.md` | Templates for person, meeting, insight, investigation notes |

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
