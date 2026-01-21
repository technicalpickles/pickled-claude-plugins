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

See `templates/vault-claude-md.md` for template.

## References

For methodology (tool-agnostic):
- `references/para.md` - PARA organizational system
- `references/zettelkasten.md` - Naming conventions
- `references/note-patterns.md` - Note templates
