---
name: obsidian
description: Obsidian vault mechanics - wiki links, .obsidian/ config, daily notes, plugins. Use when working with Obsidian vaults or structured markdown.
---

# Obsidian Skill

Tool-specific mechanics for working with Obsidian vaults.

## Vault Detection

A directory is an Obsidian vault if it contains `.obsidian/` folder.

## Wiki Links

**Syntax:** `[[Note Title]]` or `[[path/Note Title]]`

- Obsidian resolves by title match
- Can include path for disambiguation
- Aliases: `[[Note Title|display text]]`

## .obsidian/ Configuration

Obsidian stores settings in `.obsidian/` at vault root:

| File | Purpose |
|------|---------|
| `daily-notes.json` | Daily note folder and template |
| `templates.json` | Templates folder location |
| `zk-prefixer.json` | Zettelkasten/inbox settings |
| `app.json` | General settings (new file location, attachments) |
| `plugins/` | Installed plugin data |

### Parsing Config

```json
// daily-notes.json
{
  "folder": "Fleeting",
  "template": "Templates/daily"
}

// templates.json
{"folder": "Templates"}

// zk-prefixer.json
{
  "folder": "📫 Inbox",
  "template": "Templates/frontmatter"
}

// app.json
{
  "newFileFolderPath": "📫 Inbox",
  "attachmentFolderPath": "🖇 Attachments"
}
```

## Daily Notes

**Finding today's note:**
1. Read `.obsidian/daily-notes.json` for folder
2. Use format `YYYY-MM-DD.md` (Obsidian default)
3. Path: `{folder}/{YYYY-MM-DD}.md`

**Template application:**
- Obsidian applies template on note creation
- Template path from `daily-notes.json`

## Glossary Integration

If `Glossary.md` exists at vault root:
- Contains known transcription corrections
- Maps common errors to correct terms
- Used by process-daily command

## Vault CLAUDE.md

Vaults should have a `CLAUDE.md` at root describing:
- Folder structure
- Routing rules
- Naming conventions
- References to methodology (PARA, Zettelkasten)
- **Disambiguation rules** for semantically similar areas

See `templates/vault-claude-md.md` for template.

### Disambiguation Rules

When a vault has areas with semantic overlap (e.g., "tool sharpening" vs "software engineering"), the vault CLAUDE.md can include `### Disambiguation:` sections that guide routing decisions.

The routing algorithm checks for:
- **Key questions** - Decision heuristics for each area
- **Category tables** - Lists of tools/topics per area
- **Edge case mappings** - Explicit rules for ambiguous cases

See `references/routing.md` for the full disambiguation format and how to build custom rules.

## References

For methodology (tool-agnostic):
- `references/para.md` - PARA organizational system
- `references/zettelkasten.md` - Naming conventions
- `references/note-patterns.md` - Note templates
- `references/routing.md` - Routing algorithm with disambiguation support
- `references/daily-linking.md` - Linking captured notes to daily note
