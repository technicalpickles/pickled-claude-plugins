# Capture Note Format

The shape a freshly captured note takes. This is the format that has actually accumulated in the
vault, not an aspirational template - it was derived by reading ~150 real captures.

If the vault's own `CLAUDE.md` or `Templates/` specify something different, those win.

## Frontmatter

```yaml
---
status: seedling
tags: [browsers, firefox, keyboard-driven]
created: 2026-08-13
source: https://glide-browser.app/
---
```

| Field | Value |
|-------|-------|
| `status` | `seedling` for a fresh capture. This is the **zettelkasten maturity** axis (`seedling` → `budding` → `evergreen`), not the lifecycle axis. |
| `tags` | Inline list, lowercase, hyphenated, **no leading `#`** (e.g. `[person, meeting]` not `[#person, #meeting]` - an unquoted `#` at the start of a flow-sequence item or scalar value is a YAML comment and silently breaks or truncates the frontmatter). Topic tags for a concept note; a type tag (`person`, `meeting`, `idea`) where one applies. |
| `created` | `YYYY-MM-DD`. |
| `source` | The URL, file path, or origin. Omit only when there genuinely isn't one. |

### Do not hand-author these

- **Lifecycle values** (`filed`, `incubating`, `active`, `complete`, `dormant`, `abandoned`) belong
  to routed notes, not fresh captures. A capture that hasn't been routed isn't `filed` yet.
- **Pipeline states** (`ingested`, `routed`, `connected`) are set by the pipeline skills. Writing
  them by hand makes a note look processed when it isn't.
- Check the vault's canonical status vocabulary note before setting anything other than `seedling`.

### Reconciling with what sb scaffolds

`sb note create` emits provenance frontmatter:

```yaml
captured: 2026-08-14T16:49:59Z
source: manual
repo: none
branch: none
commit: none
---
```

That's built for conversation-captured insights, where git context is the useful provenance. For a
source-capture it mostly isn't. So:

- **Keep** `captured` (it's a real timestamp) and replace `source: manual` with the actual source.
- **Add** `status`, `tags`, `created`.
- **Drop** `repo`/`branch`/`commit` when they're all `none`. Keep them when the capture happened
  while working in a repo and that context matters.

## Body

```markdown
# Glide browser

A [Firefox fork](https://glide-browser.app/firefox) built for keyboard-driven browsing.

**Why I saved this:** looking for a Vimium replacement that survives Firefox updates.

- **Modal interface:** Vim-style normal and insert modes, no extension required.
- **Config:** a TypeScript config file instead of an options page, documented in the
  [config reference](https://glide-browser.app/config).
- **Status:** pre-1.0, macOS and Linux builds only.

## Related

- [[202607111019 nate berkopec|Nate Berkopec]] - same keyboard-first tooling lineage
- [[202106271223 pareto principle]] - same name as the pareto-optimal note, different idea
```

The body is these parts, in this order:

1. **`# Title`.** Sentence case, the source's own framing.
2. **What it is, in a sentence or two,** with an inline link to the primary source.
3. **`**Why I saved this:**`** followed by the user's reason, in their words. Take it from the
   request ("…for my roguelike") or from their answer when you asked. If neither gave one, write
   `**Why I saved this:** TODO`. This line is the only place the user's situation appears.
4. **The content.**
   - When the source lists 3 or more parallel items (features, options, steps, findings), write
     them as bullets with a **bold lead-in**, one item per bullet. Otherwise, a short paragraph.
   - Every tool, project, paper, or doc the source names gets an inline link, using the URL the
     source itself gives.
   - Every sentence restates something the fetched source says. Leave out anything you'd need
     outside knowledge or inference to write: implications for the user's use case, comparisons,
     numbers, history.
5. **`## Related`, last.** Only notes a search actually returned, each with a few words on why it
   relates. Bare link lists decay into unreadable piles.

## Filenames

sb generates these. Don't construct them by hand.

```
202608141249 glide-browser.md
└──┬───────┘ └──────┬──────┘
   │                └─ hyphenated slug
   └─ YYYYMMDDHHMM, then a single space
```

A hyphen between the timestamp and the slug (`202608071430-shopify-...`) is the wrong shape; it
shows up in one batch in the vault and is the outlier, not a variant.

## Notes that aren't captures

Person, meeting, investigation, and project notes have their own established shapes. See
[../../obsidian/references/note-patterns.md](../../obsidian/references/note-patterns.md). Person
notes in particular are **flat, no timestamp prefix** (`Trevor Turk.md`), because a person is a
record with a fixed address rather than a timestamped thought.
