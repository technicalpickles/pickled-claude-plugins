---
name: distill-rules
description: Review routing corrections and propose updates to vault CLAUDE.md routing rules.
allowed-tools:
  - Read(~/.claude/vaults/**/CLAUDE.md)
  - Read(~/.claude/vaults/**/.routing-memory.md)
  - Write(~/.claude/vaults/**/CLAUDE.md)
  - Write(~/.claude/vaults/**/.routing-memory.md)
  - Edit(~/.claude/vaults/**/CLAUDE.md)
  - Edit(~/.claude/vaults/**/.routing-memory.md)
  - Bash(npx @techpickles/sb:*)
---

# Distill Rules

Review accumulated routing corrections in `.routing-memory.md` and propose updates to the vault's CLAUDE.md routing rules.

See `references/routing-memory.md` for correction format and learning loop.

## Process

1. Read `.routing-memory.md` from vault root
2. Read vault CLAUDE.md

3. Analyze corrections for patterns:
   - Group corrections by destination
   - Identify repeated corrections (same type of note going to same destination)
   - Look for corrections that contradict existing CLAUDE.md rules

4. Propose updates:
   - New edge case mappings for disambiguation sections
   - New category table entries
   - New learned patterns for `.routing-memory.md`
   - Corrections to existing rules that have been consistently overridden

5. Present proposals to user:
   ```
   Found {n} patterns in {m} corrections:

   1. Add edge case: "{scenario}" -> {destination}
      Based on: {n} corrections over {date range}

   2. Add to category table: "{tool}" under {area}
      Based on: {n} corrections

   3. Update rule: "{old rule}" -> "{new rule}"
      Based on: consistently overridden {n} times

   Apply these updates?
   (A) Apply all
   (B) Review individually
   (C) Skip for now
   ```

6. Apply selected updates:
   - Edit vault CLAUDE.md with new rules
   - Move applied corrections to an `## Archived` section in `.routing-memory.md`
   - Promote stable patterns to `## Patterns Learned`

## Constraints

- Never auto-apply. Always present proposals for approval.
- Preserve existing CLAUDE.md structure and formatting
- Archive corrections, don't delete them (audit trail)
- Only propose rules backed by multiple corrections (minimum 2)
