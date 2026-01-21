# Zettelkasten Naming Convention

Timestamp-prefixed filenames for unique, sortable note identifiers.

## Format

```
YYYYMMDDHHMM short-title.md
```

**Components:**
- `YYYYMMDDHHMM` - Timestamp (year, month, day, hour, minute)
- `short-title` - 3-5 words, lowercase, hyphenated
- `.md` - Markdown extension

**Examples:**
- `202601211430 redis-session-caching.md`
- `202601211445 debugging-kafka-lag.md`
- `202601211500 meeting-platform-review.md`

## Generating Timestamps

```bash
date +"%Y%m%d%H%M"
# Output: 202601211430
```

## Benefits

1. **Unique** - Timestamp ensures no collisions
2. **Sortable** - Files sort chronologically
3. **Linkable** - Stable identifier for wiki links
4. **Discoverable** - Title in filename aids search

## Exceptions

Some note types skip the Zettelkasten prefix:

| Type | Naming | Example |
|------|--------|---------|
| Person notes | Full name | `Jane Smith.md` |
| Daily notes | Date only | `2026-01-21.md` |
| Index/MOC | Topic name | `Kafka.md` |
| Project folders | Project name | `Projects/kafka-migration/` |

## When to Use

- New permanent notes (insights, ideas, concepts)
- Meeting notes
- Investigation notes
- Extracted content from daily notes

## When NOT to Use

- Daily notes (use `YYYY-MM-DD.md`)
- Person notes (use full name)
- Templates
- Index/overview notes
