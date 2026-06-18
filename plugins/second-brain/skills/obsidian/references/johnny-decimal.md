# Johnny Decimal Reference

Johnny Decimal is an organizational system by David Thornton. It numbers folders so every note has a short, stable address. Many Obsidian vaults use it instead of (or alongside) PARA.

## The Three Levels

Johnny Decimal has exactly three folder levels. Depth stops at the ID level: there is no `NN.NN.NN`.

### Areas

**Definition:** A broad range of related topics. The widest grouping, a drawer of drawers.

**Shape:** `NN-NN ` (a number range, hyphen, then a name)

**Characteristics:**
- Spans ten possible categories (e.g. `60-69` reserves categories `60` through `69`)
- Names a domain, not a specific thing
- Holds categories, never loose notes directly

**Examples:**
- `60-69 Software & Engineering`
- `10-19 Life Admin`
- `30-39 Finances`

**In Obsidian:** A top-level folder whose name starts with a range like `60-69 `.

---

### Categories

**Definition:** A single drawer inside an area. The everyday unit you file into.

**Shape:** `NN ` (two digits, a space, then a name)

**Characteristics:**
- Belongs to exactly one area (category `67` lives in area `60-69`)
- Holds **both** loose notes AND ID subfolders
- The right home for a general or loose note about the category's topic

**Examples:**
- `67 Tools & developer experience`
- `11 Health`
- `32 Taxes`

**In Obsidian:** A folder inside an area whose name starts with two digits and a space, like `67 `.

---

### IDs

**Definition:** A specific-thing folder inside a category. The most precise address.

**Shape:** `NN.NN ` (the category number, a dot, two more digits, then a name)

**Characteristics:**
- Belongs to exactly one category (`67.01` lives in category `67`)
- Holds zettel notes; this is a leaf, it has no deeper subfolders
- The right home for a note about that one specific thing

**Examples:**
- `67.01 git`
- `67.02 docker`
- `11.03 sleep`

**In Obsidian:** A folder inside a category whose name starts with `NN.NN `, like `67.01 `.

---

## Decision Flow

When deciding where a note goes:

```
Which area's topic range does this belong to?
└── Within that area, which category (drawer) fits?
    └── Is the note about one specific thing that has (or deserves) its own ID folder?
        ├── Yes → route to the ID folder (NN.NN ...)
        └── No  → route to the category folder (NN ...), as a loose note
```

**The core heuristic:** specific note goes to an ID, loose/general note stays at the category.

A note titled "git rebase onto vs merge" belongs in `67.01 git` (specific). A note titled "thoughts on developer tooling in general" belongs at `67 Tools & developer experience` (loose). Prefer an ID destination over its parent category when the note is clearly about that one thing.

## How the Levels Compare

| Level | Shape | Example | Holds | Route here when |
|-------|-------|---------|-------|-----------------|
| Area | `NN-NN ` (range, hyphen) | `60-69 Software & Engineering` | categories | (never routed to directly) |
| Category | `NN ` (two digits, space) | `67 Tools & developer experience` | loose notes AND ID subfolders | the note is loose/general for the drawer |
| ID | `NN.NN ` (dot) | `67.01 git` | zettel notes (leaves) | the note is about that one specific thing |

You route notes to **categories** and **IDs**. Areas are the addressing scaffold; nothing files directly into an area.

## Discovering Structure

`sb vault structure` is the source of truth for which folders exist and what they are. For Johnny Decimal vaults it emits each destination with:

- `type: 'jd'` - marks the destination as Johnny Decimal (vs PARA)
- `code` - the number: `67` for a category, `67.01` for an ID
- `area` - the raw area folder name the destination sits under (e.g. `60-69 Software & Engineering`)

The sb side emits both a category and its IDs as a flat list, so routing picks granularity per note by scoring (see [routing.md](routing.md)). Never guess at numbers or paths; only suggest destinations that appear in `sb vault structure` output.

## Coexisting with PARA

A vault mid-migration can hold both Johnny Decimal and PARA folders at once. `sb vault structure` tags each destination's `type` so routing can score them side by side. Don't assume a vault is one or the other; route to whatever exists. See [para.md](para.md) for the PARA side.
