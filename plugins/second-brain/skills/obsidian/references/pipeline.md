# Processing Pipeline Reference

The inbox processing pipeline breaks into five independent stages. Each stage is a skill that can be invoked individually or composed by the `process-inbox` orchestrator.

## Stages

| Stage | Skill | Input Status | Output Status | Confidence |
|-------|-------|-------------|---------------|------------|
| 1. Ingest | `ingest` | `raw` | `ingested` | High (mechanical) |
| 2. Enrich | `enrich` | `ingested` | `enriched` | High (prose cleanup) |
| 3. Route | `route` | `enriched` | `routed` or `pending-review` | Variable |
| 4. Connect | `connect` | `routed` | `connected` | Variable |
| 5. Link Daily | `link-daily` | `connected` | `complete` | High (mechanical) |

## Status Values

Each note carries its pipeline state in frontmatter:

| Status | Meaning |
|--------|---------|
| `raw` | Just landed in inbox. Session notes file with bullet points. |
| `ingested` | Individual insights extracted from session note into separate files. |
| `enriched` | Proper zettelkasten note with clean prose and title. |
| `routed` | Moved to destination folder. |
| `connected` | Related notes linked via `## Related` section. |
| `complete` | All stages done, daily note linked. |
| `pending-review` | Route stage needs human input (low confidence). |

Notes without a `status` field are treated as `raw`.

## Status Flow

```
raw -> ingested -> enriched -> routed -> connected -> complete
                          \-> pending-review (low confidence at route stage)
```

After human resolves `pending-review` (picks a destination), status moves to `routed` and continues through the pipeline.

## Note Types

| Type | Frontmatter `type` | Created By | Processed By |
|------|-------------------|------------|--------------|
| Session notes | `session-notes` | `/insight`, `/distill-conversation` | `ingest` stage |
| Insight | `insight` | `ingest` stage | `enrich` through `link-daily` |

Session notes files contain multiple bullet points from a working session. The `ingest` stage splits them into individual insight notes.

## Confidence Model

The `route` stage scores destinations using three sources (priority order):

1. Recent corrections in `.routing-memory.md` (recency wins)
2. Learned patterns in `.routing-memory.md`
3. Vault CLAUDE.md disambiguation rules + generic signals

Notes scoring above the `auto-route-threshold` (from `.routing-memory.md` frontmatter, default 70) are auto-routed. Notes below the threshold get `pending-review`.

See `references/routing-memory.md` for the correction and learning loop.
See `references/routing.md` for the scoring algorithm.
