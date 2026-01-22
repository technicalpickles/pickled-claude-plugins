# PARA Method Reference

PARA is an organizational system by Tiago Forte. Many Obsidian vaults use it or variations.

## The Four Categories

### Projects

**Definition:** A series of tasks linked to a goal, with a deadline.

**Characteristics:**
- Has a clear outcome
- Has a timeframe (even if fuzzy)
- Requires multiple work sessions
- Is "completable"

**Examples:**
- Launch new feature
- Plan vacation
- Write blog post
- Complete course

**In Obsidian:** `Projects/` folder, often with subfolders per project

---

### Areas

**Definition:** A sphere of activity with a standard to be maintained over time.

**Characteristics:**
- Ongoing responsibility
- No end date
- Has standards to uphold
- Part of your identity/role

**Examples:**
- Health
- Finances
- Career
- Family
- Specific work domain (e.g., "Kafka infrastructure")

**In Obsidian:** `Areas/` folder, subfolders by area

---

### Resources

**Definition:** A topic or theme of ongoing interest.

**Characteristics:**
- Reference material
- Not tied to action
- Collected over time
- Useful for multiple contexts

**Examples:**
- Programming languages
- Cooking recipes
- Book notes
- Industry knowledge

**In Obsidian:** `Resources/` folder, subfolders by topic

---

### Archive

**Definition:** Inactive items from the other three categories.

**Characteristics:**
- No longer active
- Kept for reference
- Searchable when needed
- Out of sight day-to-day

**Examples:**
- Completed projects
- Former areas of responsibility
- Outdated resources

**In Obsidian:** `Archive/` folder, mirroring original structure

---

## Decision Flow

When deciding where something goes:

```
Is it actionable?
├── No → Is it interesting/useful reference?
│        ├── Yes → Resources
│        └── No → Maybe don't keep it
└── Yes → Does it have a deadline/outcome?
         ├── Yes → Projects
         └── No → Is it ongoing responsibility?
                  ├── Yes → Areas
                  └── No → Probably a Project (define the outcome)
```

## Common Extensions

Many vaults extend PARA with:

| Folder | Purpose |
|--------|---------|
| **Inbox** | Capture point before organizing |
| **Daily/Fleeting** | Daily notes, temporary captures |
| **Templates** | Note templates |
| **Attachments** | Media files |

## Projects vs Areas

This is the most common confusion:

| Projects | Areas |
|----------|-------|
| "Launch Kafka migration" | "Kafka infrastructure" |
| "Hire new team member" | "Team management" |
| "Set up home office" | "Home" |
| "Write Q1 goals" | "Career development" |

**Key test:** Can you "complete" it?
- Yes → Project
- No → Area

## Moving Between Categories

Content naturally flows:

1. **Inbox → anywhere**: Initial captures get sorted
2. **Projects → Archive**: When completed
3. **Areas → Archive**: When no longer your responsibility
4. **Projects → Areas**: When scope grows to ongoing (rare)

## Vault-Specific Variations

Always check the vault's CLAUDE.md for how they've adapted PARA:
- Different folder names (e.g., `1.🚀 Projects/`)
- Additional categories
- Different nesting strategies
- Modified decision criteria
